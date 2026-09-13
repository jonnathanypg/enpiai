"""
Club Routes - Management and public endpoints for Distributor Nutrition Clubs.
Supports:
- Public Club Microsite catalog & ordering
- Location & Maps (Google Maps & Apple Maps)
- Preparation menu customization (flavors, toppings, extras)
- Real-time order dispatch via WhatsApp & Database CRM
"""
import logging
import urllib.parse
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.distributor import Distributor
from models.product import Product
from models.club_order import ClubOrder
from models.lead import Lead, LeadSource

logger = logging.getLogger(__name__)

club_bp = Blueprint('club', __name__)


def _get_current_distributor():
    """Helper: get the distributor associated with the current JWT user"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or not user.distributor_id:
        return None, None
    distributor = Distributor.query.get(user.distributor_id)
    return user, distributor


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC ENDPOINTS (Microsite / E-Commerce)
# ─────────────────────────────────────────────────────────────────────────────

@club_bp.route('/public/<string:distributor_ref>', methods=['GET'])
def get_public_club(distributor_ref):
    """
    Public endpoint: Get Nutrition Club profile, location, schedule, and menu.
    Prospects access this via /club/<herbalife_id> or /club/<id>.
    """
    db.session.rollback()
    try:
        # Lookup distributor by herbalife_id or numeric ID
        distributor = Distributor.query.filter_by(herbalife_id=distributor_ref).first()
        if not distributor and distributor_ref.isdigit():
            distributor = Distributor.query.get(int(distributor_ref))

        if not distributor:
            return jsonify({'error': 'Nutrition Club not found'}), 404

        # Fetch active products for the club menu
        products = Product.query.filter_by(
            distributor_id=distributor.id,
            is_available=True
        ).order_by(Product.display_order.asc(), Product.category.asc(), Product.name.asc()).all()

        club_info = distributor.get_club_dict()
        
        # Categorized preparations
        categories = [
            {'id': 'all', 'label': 'Todos', 'icon': '✨'},
            {'id': 'batidos', 'label': 'Batidos Proteicos', 'icon': '🥤'},
            {'id': 'tes_bebidas', 'label': 'Tés & Bebidas Herbales', 'icon': '🍵'},
            {'id': 'waffles_bowls', 'label': 'Waffles & Bowls', 'icon': '🧇'},
            {'id': 'combos', 'label': 'Combos 3 Pasos', 'icon': '🥣'},
            {'id': 'snacks', 'label': 'Snacks & Suplementos', 'icon': '🥗'},
        ]

        return jsonify({
            'data': {
                'club': club_info,
                'categories': categories,
                'products': [p.to_dict() for p in products],
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting public club {distributor_ref}: {e}")
        return jsonify({'error': str(e)}), 500


@club_bp.route('/public/<string:distributor_ref>/order', methods=['POST'])
def submit_club_order(distributor_ref):
    """
    Public endpoint: Place a customer order in the Nutrition Club.
    Saves the order in DB, links/creates CRM Lead, and returns formatted WhatsApp redirect link.
    """
    db.session.rollback()
    try:
        distributor = Distributor.query.filter_by(herbalife_id=distributor_ref).first()
        if not distributor and distributor_ref.isdigit():
            distributor = Distributor.query.get(int(distributor_ref))

        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        if not data or not data.get('customer_name') or not data.get('items'):
            return jsonify({'error': 'Customer name and items are required'}), 400

        customer_name = data.get('customer_name').strip()
        customer_phone = (data.get('customer_phone') or '').strip()
        customer_email = (data.get('customer_email') or '').strip()
        delivery_type = data.get('delivery_type', 'dine_in') # dine_in, pickup, delivery
        items = data.get('items', [])
        notes = data.get('notes', '')
        subtotal = float(data.get('subtotal') or 0.0)
        total = float(data.get('total') or subtotal)
        currency = data.get('currency', 'USD')

        # Auto-create or find lead in CRM
        lead = None
        if customer_phone:
            phone_h = Lead.generate_phone_hash(customer_phone)
            lead = Lead.query.filter_by(distributor_id=distributor.id, phone_hash=phone_h).first()
        if not lead and customer_email:
            email_h = Lead.generate_hash(customer_email)
            lead = Lead.query.filter_by(distributor_id=distributor.id, email_hash=email_h).first()

        if not lead:
            lead = Lead(
                distributor_id=distributor.id,
                first_name=customer_name,
                phone=customer_phone,
                email=customer_email,
                source=LeadSource.WEB_FORM,
                notes=f"Pedido en Club de Nutrición: {delivery_type}"
            )
            db.session.add(lead)
            db.session.flush()

        # Create Club Order
        order = ClubOrder(
            distributor_id=distributor.id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            delivery_type=delivery_type,
            items=items,
            subtotal=subtotal,
            total=total,
            currency=currency,
            notes=notes,
            status='pending'
        )
        order.generate_order_number()
        db.session.add(order)
        db.session.commit()
        logger.info(f"New Club Order {order.order_number} created for distributor {distributor.id}")

        # Build WhatsApp Message Text
        delivery_labels = {
            'dine_in': '🍽️ Consumo en Club (Mesa/Barra)',
            'pickup': '🥡 Para Llevar / Retiro',
            'delivery': '🛵 Entrega a Domicilio / Oficina'
        }
        delivery_text = delivery_labels.get(delivery_type, delivery_type)

        lines = [
            f"🌿 *NUEVO PEDIDO - {distributor.club_name or 'CLUB DE NUTRICIÓN'}* 🌿",
            f"📋 *Orden:* #{order.order_number}",
            f"👤 *Cliente:* {customer_name}",
        ]
        if customer_phone:
            lines.append(f"📱 *Teléfono:* {customer_phone}")
        lines.append(f"📍 *Modalidad:* {delivery_text}")
        lines.append("\n🛒 *DETALLE DEL PEDIDO:*")

        for idx, item in enumerate(items, 1):
            qty = item.get('quantity', 1)
            name = item.get('name', 'Producto')
            price = item.get('price', 0.0)
            item_total = item.get('total', float(qty) * float(price))
            flavor = item.get('flavor')
            toppings = item.get('toppings') or []
            item_notes = item.get('notes')

            item_line = f"{idx}. *{qty}x {name}* - ${item_total:.2f}"
            if flavor:
                item_line += f"\n   • Sabor: {flavor}"
            if toppings:
                item_line += f"\n   • Toppings: {', '.join(toppings)}"
            if item_notes:
                item_line += f"\n   • Nota: {item_notes}"
            lines.append(item_line)

        lines.append(f"\n💰 *TOTAL A PAGAR:* ${total:.2f} {currency}")
        if notes:
            lines.append(f"📝 *Observaciones:* {notes}")

        if distributor.club_address:
            lines.append(f"\n📍 *Ubicación del Club:* {distributor.club_address}")
            if distributor.get_google_maps_url():
                lines.append(f"🗺️ Google Maps: {distributor.get_google_maps_url()}")

        full_message = "\n".join(lines)
        encoded_msg = urllib.parse.quote(full_message)

        # Target distributor phone
        target_phone = distributor.club_phone or distributor.whatsapp_phone or distributor.phone or ""
        clean_target_phone = "".join(filter(str.isdigit, target_phone))

        whatsapp_url = f"https://wa.me/{clean_target_phone}?text={encoded_msg}" if clean_target_phone else f"https://wa.me/?text={encoded_msg}"

        return jsonify({
            'data': {
                'order': order.to_dict(),
                'whatsapp_url': whatsapp_url,
                'message_preview': full_message
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating club order: {e}")
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# DISTRIBUTOR MANAGEMENT ENDPOINTS (JWT Required)
# ─────────────────────────────────────────────────────────────────────────────

@club_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_club_settings():
    """Get distributor's Nutrition Club settings"""
    db.session.rollback()
    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        return jsonify({'data': distributor.get_club_dict()}), 200
    except Exception as e:
        logger.error(f"Get club settings error: {e}")
        return jsonify({'error': str(e)}), 500


@club_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_club_settings():
    """Update distributor's Nutrition Club profile and location"""
    db.session.rollback()
    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        updatable = [
            'club_name', 'club_slogan', 'club_address', 'club_city',
            'club_schedule', 'club_phone', 'club_latitude', 'club_longitude',
            'club_banner_url', 'club_logo_url', 'club_is_active',
            'club_amenities', 'club_announcement'
        ]

        for field in updatable:
            if field in data:
                setattr(distributor, field, data[field])

        db.session.commit()
        logger.info(f"Distributor {distributor.id} Nutrition Club settings updated")

        return jsonify({'data': distributor.get_club_dict()}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update club settings error: {e}")
        return jsonify({'error': str(e)}), 500


@club_bp.route('/products', methods=['GET'])
@jwt_required()
def list_club_products():
    """List club preparations / products for authenticated distributor"""
    db.session.rollback()
    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        category = request.args.get('category')
        query = Product.query.filter_by(distributor_id=distributor.id)

        if category and category != 'all':
            query = query.filter_by(category=category)

        products = query.order_by(Product.display_order.asc(), Product.category.asc(), Product.name.asc()).all()

        return jsonify({'data': [p.to_dict() for p in products]}), 200
    except Exception as e:
        logger.error(f"List club products error: {e}")
        return jsonify({'error': str(e)}), 500


@club_bp.route('/products', methods=['POST'])
@jwt_required()
def create_club_product():
    """Create a new preparation or product in the Club menu"""
    db.session.rollback()
    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({'error': 'Product name is required'}), 400

        product = Product(
            distributor_id=distributor.id,
            name=data['name'],
            sku=data.get('sku'),
            category=data.get('category', 'batidos'),
            description=data.get('description'),
            price=float(data.get('price') or 0.0),
            currency=data.get('currency', 'USD'),
            image_url=data.get('image_url'),
            is_available=data.get('is_available', True),
            is_club_menu=True,
            protein_grams=float(data.get('protein_grams')) if data.get('protein_grams') is not None else None,
            calories=int(data.get('calories')) if data.get('calories') is not None else None,
            preparation_time_min=int(data.get('preparation_time_min') or 5),
            customization_options=data.get('customization_options') or {},
            benefits=data.get('benefits') or [],
            ingredients=data.get('ingredients'),
            usage_instructions=data.get('usage_instructions'),
            display_order=int(data.get('display_order') or 0)
        )
        db.session.add(product)
        db.session.commit()
        logger.info(f"Club product '{product.name}' created by distributor {distributor.id}")

        return jsonify({'data': product.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create club product error: {e}")
        return jsonify({'error': str(e)}), 500


@club_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_club_product(product_id):
    """Update a preparation or product in the Club menu"""
    db.session.rollback()
    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        product = Product.query.filter_by(id=product_id, distributor_id=distributor.id).first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        fields = [
            'name', 'sku', 'category', 'description', 'price', 'currency',
            'image_url', 'is_available', 'protein_grams', 'calories',
            'preparation_time_min', 'customization_options', 'benefits',
            'ingredients', 'usage_instructions', 'display_order'
        ]

        for f in fields:
            if f in data:
                val = data[f]
                if f in ['price', 'protein_grams'] and val is not None:
                    val = float(val)
                elif f in ['calories', 'preparation_time_min', 'display_order'] and val is not None:
                    val = int(val)
                setattr(product, f, val)

        db.session.commit()
        return jsonify({'data': product.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update club product error: {e}")
        return jsonify({'error': str(e)}), 500


@club_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_club_product(product_id):
    """Delete a preparation from the Club menu"""
    db.session.rollback()
    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        product = Product.query.filter_by(id=product_id, distributor_id=distributor.id).first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete club product error: {e}")
        return jsonify({'error': str(e)}), 500


@club_bp.route('/seed-menu', methods=['POST'])
@jwt_required()
def seed_club_menu():
    """Seed typical Nutrition Club preparations and recipes for 1-click startup"""
    db.session.rollback()
    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        STARTER_MENU = [
            {
                "name": "Batido Nutricional Fórmula 1 (Especial)",
                "category": "batidos",
                "price": 3.50,
                "protein_grams": 24.0,
                "calories": 210,
                "description": "Batido cremoso rico en 21 vitaminas, minerales y 24g de proteína de alta calidad. El desayuno perfecto.",
                "image_url": "https://images.unsplash.com/photo-1553787499-6f9133860278?w=800&auto=format&fit=crop&q=80",
                "customization_options": {
                    "flavors": ["Cookies & Cream", "Chocolate Belga", "Fresa Silvestre", "Vainilla Francesa", "Café Latte", "Plátano Caramelo"],
                    "toppings": ["Granola Crunch", "Semillas de Chía", "Coco Tostado", "Canela en Polvo"],
                    "temperature": ["Frappé con Hielo", "Frío", "Tibio"]
                },
                "benefits": ["24g de Proteína", "21 Vitaminas y Minerales", "Sensación de Saciedad"]
            },
            {
                "name": "Mega Té NRG Guaraná & Antioxidante",
                "category": "tes_bebidas",
                "price": 2.50,
                "protein_grams": 0.0,
                "calories": 15,
                "description": "Explosión de energía natural con té verde, té negro, extracto de guaraná y cáscara de limón. Alerta mental al instante.",
                "image_url": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=800&auto=format&fit=crop&q=80",
                "customization_options": {
                    "flavors": ["Frutos Rojos", "Limón Cítrico", "Durazno", "Manzana Verde"],
                    "temperature": ["Bien Frío con Hielo", "Caliente Revitalizante"]
                },
                "benefits": ["Energía Instantánea", "Cero Azúcar Añadida", "Poder Antioxidante"]
            },
            {
                "name": "Herbal Aloe Concentrado (Shot Digestivo)",
                "category": "tes_bebidas",
                "price": 2.00,
                "protein_grams": 0.0,
                "calories": 5,
                "description": "Bebida purificante a base de sábila orgánica que desinflama el tracto digestivo y promueve la hidratación profunda.",
                "image_url": "https://images.unsplash.com/photo-1546173159-315724a31696?w=800&auto=format&fit=crop&q=80",
                "customization_options": {
                    "flavors": ["Mango Tropical", "Mandarina", "Original Cítrico", "Uva"],
                    "temperature": ["Frío", "Con Agua con Gas"]
                },
                "benefits": ["Alivia la Pesadez", "Salud Intestinal", "Cero Calorías"]
            },
            {
                "name": "Waffle Proteico Gourmet",
                "category": "waffles_bowls",
                "price": 4.50,
                "protein_grams": 26.0,
                "calories": 280,
                "description": "Waffle recién horneado hecho con masa proteica F1 y proteína aislada. Crujiente por fuera, suave por dentro.",
                "image_url": "https://images.unsplash.com/photo-1562376552-0d160a2f238d?w=800&auto=format&fit=crop&q=80",
                "customization_options": {
                    "flavors": ["Masa de Vainilla", "Masa de Chocolate", "Masa Cookies"],
                    "toppings": ["Fresas Frescas", "Miel Sin Azúcar", "Topping Proteico Choco", "Almendras Fileteadas"],
                    "extras": ["Doble Proteína (+1.00)", "Colágeno Booster (+1.50)"]
                },
                "benefits": ["26g de Proteína", "Sin Harinas Refinadas", "Delicioso y Saludable"]
            },
            {
                "name": "Combo Desayuno Saludable 3 Pasos",
                "category": "combos",
                "price": 6.50,
                "protein_grams": 25.0,
                "calories": 230,
                "description": "El protocolo completo del club: 1) Shot de Aloe Vera + 2) Té Energizante Termogénico + 3) Batido Nutricional Fórmula 1.",
                "image_url": "https://images.unsplash.com/photo-1494859802809-d069c3b71a8a?w=800&auto=format&fit=crop&q=80",
                "customization_options": {
                    "flavors": ["Batido a Elección", "Sabor de Aloe", "Sabor de Té"],
                    "temperature": ["Frío", "Combinado"]
                },
                "benefits": ["Limpieza + Energía + Nutrición", "Ahorro Especial", "Plan Completo"]
            },
            {
                "name": "Chupapanzas Herbal Quema-Grasa",
                "category": "tes_bebidas",
                "price": 3.50,
                "protein_grams": 5.0,
                "calories": 25,
                "description": "Fórmula legendaria de club: Té Concentrado + Aloe Vera + Fibra Activa de Manzana para aplanar el abdomen y mejorar digestión.",
                "image_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=800&auto=format&fit=crop&q=80",
                "customization_options": {
                    "flavors": ["Manzana Cítrica", "Mango Guaraná", "Frambuesa"],
                    "temperature": ["Frío Frappé", "Caliente Detox"]
                },
                "benefits": ["Acelera el Metabolismo", "Fibra Digestiva 5g", "Efecto Desinflamante"]
            },
            {
                "name": "Protein Bowl de Avena & Semillas",
                "category": "waffles_bowls",
                "price": 4.00,
                "protein_grams": 22.0,
                "calories": 250,
                "description": "Bowl energizante con base de batido espeso, avena integral, chía, semillas de calabaza y fruta fresca de temporada.",
                "image_url": "https://images.unsplash.com/photo-1590301157890-4810ed352733?w=800&auto=format&fit=crop&q=80",
                "customization_options": {
                    "flavors": ["Base Fresa Plátano", "Base Chocolate Avena", "Base Vainilla Chía"],
                    "toppings": ["Frutos Rojos", "Mantequilla de Maní Natural", "Coco Rallado"]
                },
                "benefits": ["Fibra y Proteína", "Energía Duradera", "Rico en Antioxidantes"]
            },
            {
                "name": "Barra de Proteína Deluxe",
                "category": "snacks",
                "price": 2.50,
                "protein_grams": 10.0,
                "calories": 140,
                "description": "Snack proteico crujiente bañado en chocolate oscuro para calmar el antojo dulce entre horas sin romper tu plan.",
                "image_url": "https://images.unsplash.com/photo-1622484216850-258055694218?w=800&auto=format&fit=crop&q=80",
                "customization_options": {
                    "flavors": ["Vainilla Almendra", "Chocolate Cacahuate", "Cítrico Limón"]
                },
                "benefits": ["10g Proteína", "140 Calorías", "Snack Rápido"]
            }
        ]

        created_count = 0
        for item_data in STARTER_MENU:
            existing = Product.query.filter_by(
                distributor_id=distributor.id,
                name=item_data['name']
            ).first()

            if not existing:
                p = Product(
                    distributor_id=distributor.id,
                    name=item_data['name'],
                    category=item_data['category'],
                    price=item_data['price'],
                    protein_grams=item_data['protein_grams'],
                    calories=item_data['calories'],
                    description=item_data['description'],
                    image_url=item_data['image_url'],
                    customization_options=item_data['customization_options'],
                    benefits=item_data['benefits'],
                    is_available=True,
                    is_club_menu=True,
                    preparation_time_min=5,
                    display_order=created_count
                )
                db.session.add(p)
                created_count += 1

        db.session.commit()
        logger.info(f"Seeded {created_count} starter menu products for distributor {distributor.id}")

        products = Product.query.filter_by(distributor_id=distributor.id).all()
        return jsonify({
            'message': f'Se agregaron {created_count} recetas y preparaciones típicas a tu club.',
            'data': [p.to_dict() for p in products]
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Seed club menu error: {e}")
        return jsonify({'error': str(e)}), 500


@club_bp.route('/orders', methods=['GET'])
@jwt_required()
def list_club_orders():
    """List orders placed at the Nutrition Club"""
    db.session.rollback()
    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = ClubOrder.query.filter_by(distributor_id=distributor.id)
        if status and status != 'all':
            query = query.filter_by(status=status)

        pagination = query.order_by(ClubOrder.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'data': [o.to_dict() for o in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
    except Exception as e:
        logger.error(f"List club orders error: {e}")
        return jsonify({'error': str(e)}), 500


@club_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    """Update order status (confirmed, preparing, ready, delivered, cancelled)"""
    db.session.rollback()
    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        order = ClubOrder.query.filter_by(id=order_id, distributor_id=distributor.id).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        data = request.get_json()
        new_status = data.get('status')
        if not new_status:
            return jsonify({'error': 'status is required'}), 400

        order.status = new_status
        db.session.commit()
        logger.info(f"Club order {order.id} status updated to {new_status}")

        return jsonify({'data': order.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update order status error: {e}")
        return jsonify({'error': str(e)}), 500
