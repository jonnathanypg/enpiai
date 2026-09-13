import json
import logging
from typing import List, Optional
from langchain_core.tools import StructuredTool
from .base_skill import BaseSkill
from extensions import db, ctx
from models.distributor import Distributor
from models.product import Product
from models.club_order import ClubOrder

logger = logging.getLogger(__name__)


class ClubSkill(BaseSkill):
    """
    Skill to manage the Distributor's Nutrition Club (Club de Nutrición),
    including club profile, location, menu preparations, recipes, pricing, and orders.
    """
    def __init__(self):
        self._name = "club"
        self._description = "Manage Distributor Nutrition Club (Club de Nutrición), profile, location, menu, recipes, prices, and orders."

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.get_club_info,
                name="get_club_info",
                description="Get current Nutrition Club information (name, address, schedule, map links, public microsite link, active menu count)."
            ),
            StructuredTool.from_function(
                func=self.update_club_profile,
                name="update_club_profile",
                description="Configure or update the Nutrition Club profile, location, address, city, opening hours/schedule, phone, or slogan."
            ),
            StructuredTool.from_function(
                func=self.list_club_products,
                name="list_club_products",
                description="List all products, preparations, waffles, shakes, and drinks in the Nutrition Club catalog with their prices."
            ),
            StructuredTool.from_function(
                func=self.create_club_product,
                name="create_club_product",
                description="Create a new preparation or product in the Nutrition Club menu (e.g. Waffle Proteico, Batido Especial, Mega Té, etc.)."
            ),
            StructuredTool.from_function(
                func=self.update_club_product,
                name="update_club_product",
                description="Update price, availability, description, or recipe details of a Club menu product."
            ),
            StructuredTool.from_function(
                func=self.delete_club_product,
                name="delete_club_product",
                description="Remove a product or preparation from the Nutrition Club catalog."
            ),
            StructuredTool.from_function(
                func=self.seed_default_club_menu,
                name="seed_default_club_menu",
                description="Populate the Club menu with the 8 standard and popular Herbalife club recipes (shakes, teas, waffles, combos) automatically."
            ),
            StructuredTool.from_function(
                func=self.list_recent_club_orders,
                name="list_recent_club_orders",
                description="Check recent customer orders placed in the Nutrition Club microsite."
            ),
        ]

    def _get_distributor(self) -> Optional[Distributor]:
        return getattr(ctx, 'current_company', None)

    def get_club_info(self) -> str:
        """Retrieve Nutrition Club details, map links, and public link"""
        db.session.rollback()
        distributor = self._get_distributor()
        if not distributor:
            return "Error: No distributor context found."

        club = distributor.get_club_dict()
        product_count = Product.query.filter_by(distributor_id=distributor.id, is_available=True).count()
        microsite_link = f"https://enpi.click/club/{distributor.herbalife_id or distributor.id}"

        response = [
            f"🏢 **{club['club_name']}**",
            f"• Eslogan: {club['club_slogan']}",
            f"• Dirección: {club['club_address'] or 'No configurada'} ({club['club_city'] or 'Ciudad no especificada'})",
            f"• Horario de Atención: {club['club_schedule']}",
            f"• Teléfono / WhatsApp: {club['club_phone'] or 'No configurado'}",
            f"• Preparaciones activas en menú: {product_count}",
            f"• Enlace Público del Micrositio: {microsite_link}",
        ]
        if club.get('google_maps_url'):
            response.append(f"• 📍 Google Maps: {club['google_maps_url']}")
        if club.get('apple_maps_url'):
            response.append(f"• 🗺️ Apple Maps: {club['apple_maps_url']}")

        return "\n".join(response)

    def update_club_profile(
        self,
        club_name: Optional[str] = None,
        club_address: Optional[str] = None,
        club_city: Optional[str] = None,
        club_schedule: Optional[str] = None,
        club_slogan: Optional[str] = None,
        club_phone: Optional[str] = None,
        club_latitude: Optional[float] = None,
        club_longitude: Optional[float] = None,
    ) -> str:
        """Update distributor club profile details"""
        db.session.rollback()
        distributor = self._get_distributor()
        if not distributor:
            return "Error: No distributor context found."

        updated = []
        if club_name is not None:
            distributor.club_name = club_name
            updated.append(f"Nombre: '{club_name}'")
        if club_address is not None:
            distributor.club_address = club_address
            updated.append(f"Dirección: '{club_address}'")
        if club_city is not None:
            distributor.club_city = club_city
            updated.append(f"Ciudad: '{club_city}'")
        if club_schedule is not None:
            distributor.club_schedule = club_schedule
            updated.append(f"Horario: '{club_schedule}'")
        if club_slogan is not None:
            distributor.club_slogan = club_slogan
            updated.append(f"Eslogan: '{club_slogan}'")
        if club_phone is not None:
            distributor.club_phone = club_phone
            updated.append(f"Teléfono: '{club_phone}'")
        if club_latitude is not None:
            distributor.club_latitude = club_latitude
            updated.append(f"Latitud: {club_latitude}")
        if club_longitude is not None:
            distributor.club_longitude = club_longitude
            updated.append(f"Longitud: {club_longitude}")

        if not updated:
            return "No se especificaron cambios para actualizar el club."

        try:
            db.session.commit()
            return f"✅ Club de Nutrición actualizado exitosamente:\n- " + "\n- ".join(updated)
        except Exception as e:
            db.session.rollback()
            return f"Error al guardar los cambios: {str(e)}"

    def list_club_products(self, category: Optional[str] = None) -> str:
        """List products and preparations in the club catalog"""
        db.session.rollback()
        distributor = self._get_distributor()
        if not distributor:
            return "Error: No distributor context found."

        query = Product.query.filter_by(distributor_id=distributor.id)
        if category and category.lower() != 'all':
            query = query.filter_by(category=category.lower())

        products = query.order_by(Product.category.asc(), Product.name.asc()).all()
        if not products:
            return "Tu club aún no tiene preparaciones o productos registrados. Puedes pedirme que cargue el menú típico ('Carga el menú de inicio') o crear uno nuevo."

        lines = [f"📋 **Menú del Club ({len(products)} preparaciones):**"]
        for p in products:
            status = "✅" if p.is_available else "❌ (Agotado)"
            protein = f" • {p.protein_grams}g proteína" if p.protein_grams else ""
            cals = f" • {p.calories} kcal" if p.calories else ""
            lines.append(f"- ID {p.id}: **{p.name}** [Cat: {p.category}] - ${p.price:.2f}{protein}{cals} {status}")

        return "\n".join(lines)

    def create_club_product(
        self,
        name: str,
        price: float,
        category: str = "batidos",
        description: Optional[str] = None,
        protein_grams: Optional[float] = None,
        calories: Optional[int] = None,
        flavors: Optional[str] = None,
        toppings: Optional[str] = None,
    ) -> str:
        """Add a new product or preparation to the Club menu"""
        db.session.rollback()
        distributor = self._get_distributor()
        if not distributor:
            return "Error: No distributor context found."

        custom_opt = {}
        if flavors:
            custom_opt['flavors'] = [f.strip() for f in flavors.split(',') if f.strip()]
        if toppings:
            custom_opt['toppings'] = [t.strip() for t in toppings.split(',') if t.strip()]

        cat_clean = category.lower().replace(' ', '_')
        valid_cats = ['batidos', 'tes_bebidas', 'waffles_bowls', 'combos', 'snacks', 'suplementos']
        if cat_clean not in valid_cats:
            if 'waffle' in cat_clean or 'bowl' in cat_clean or 'panqueque' in cat_clean:
                cat_clean = 'waffles_bowls'
            elif 'te' in cat_clean or 'té' in cat_clean or 'bebida' in cat_clean or 'aloe' in cat_clean:
                cat_clean = 'tes_bebidas'
            elif 'combo' in cat_clean or 'desayuno' in cat_clean:
                cat_clean = 'combos'
            elif 'snack' in cat_clean or 'barra' in cat_clean:
                cat_clean = 'snacks'
            else:
                cat_clean = 'batidos'

        # Default images by category if none provided
        cat_images = {
            'batidos': 'https://images.unsplash.com/photo-1553787499-6f9133860278?w=800&auto=format&fit=crop&q=80',
            'tes_bebidas': 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=800&auto=format&fit=crop&q=80',
            'waffles_bowls': 'https://images.unsplash.com/photo-1562376552-0d160a2f238d?w=800&auto=format&fit=crop&q=80',
            'combos': 'https://images.unsplash.com/photo-1494859802809-d069c3b71a8a?w=800&auto=format&fit=crop&q=80',
            'snacks': 'https://images.unsplash.com/photo-1622484216850-258055694218?w=800&auto=format&fit=crop&q=80',
            'suplementos': 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=800&auto=format&fit=crop&q=80'
        }

        product = Product(
            distributor_id=distributor.id,
            name=name.strip(),
            category=cat_clean,
            price=float(price),
            description=description or f"Deliciosa preparación nutritiva de {name}.",
            protein_grams=float(protein_grams) if protein_grams is not None else None,
            calories=int(calories) if calories is not None else None,
            image_url=cat_images.get(cat_clean),
            customization_options=custom_opt,
            is_available=True,
            is_club_menu=True
        )
        db.session.add(product)

        try:
            db.session.commit()
            return f"✅ Preparación creada exitosamente: **{product.name}** a ${product.price:.2f} (Categoría: {product.category}). Ya está visible en tu microsite."
        except Exception as e:
            db.session.rollback()
            return f"Error al crear la preparación: {str(e)}"

    def update_club_product(
        self,
        product_name_or_id: str,
        new_price: Optional[float] = None,
        is_available: Optional[bool] = None,
        new_description: Optional[str] = None,
    ) -> str:
        """Update price, availability or description of a club item"""
        db.session.rollback()
        distributor = self._get_distributor()
        if not distributor:
            return "Error: No distributor context found."

        # Match by ID or Name
        product = None
        if str(product_name_or_id).isdigit():
            product = Product.query.filter_by(id=int(product_name_or_id), distributor_id=distributor.id).first()

        if not product:
            product = Product.query.filter(
                Product.distributor_id == distributor.id,
                Product.name.ilike(f"%{product_name_or_id}%")
            ).first()

        if not product:
            return f"No se encontró ningún producto que coincida con '{product_name_or_id}'."

        changes = []
        if new_price is not None:
            product.price = float(new_price)
            changes.append(f"Precio: ${new_price:.2f}")
        if is_available is not None:
            product.is_available = is_available
            changes.append(f"Disponibilidad: {'Disponible' if is_available else 'Agotado'}")
        if new_description is not None:
            product.description = new_description
            changes.append(f"Descripción actualizada")

        if not changes:
            return f"No se especificaron cambios para '{product.name}'."

        try:
            db.session.commit()
            return f"✅ Producto '{product.name}' actualizado:\n- " + "\n- ".join(changes)
        except Exception as e:
            db.session.rollback()
            return f"Error al actualizar: {str(e)}"

    def delete_club_product(self, product_name_or_id: str) -> str:
        """Delete an item from the club catalog"""
        db.session.rollback()
        distributor = self._get_distributor()
        if not distributor:
            return "Error: No distributor context found."

        product = None
        if str(product_name_or_id).isdigit():
            product = Product.query.filter_by(id=int(product_name_or_id), distributor_id=distributor.id).first()

        if not product:
            product = Product.query.filter(
                Product.distributor_id == distributor.id,
                Product.name.ilike(f"%{product_name_or_id}%")
            ).first()

        if not product:
            return f"No se encontró el producto '{product_name_or_id}' para eliminar."

        name = product.name
        db.session.delete(product)
        try:
            db.session.commit()
            return f"🗑️ Se eliminó '{name}' del menú de tu club."
        except Exception as e:
            db.session.rollback()
            return f"Error al eliminar producto: {str(e)}"

    def seed_default_club_menu(self) -> str:
        """Seed typical Herbalife Nutrition Club preparations"""
        db.session.rollback()
        distributor = self._get_distributor()
        if not distributor:
            return "Error: No distributor context found."

        from routes.club import seed_club_menu
        # Run seeding logic directly
        STARTER_MENU = [
            {"name": "Batido Nutricional Fórmula 1 (Especial)", "category": "batidos", "price": 3.50, "protein_grams": 24.0, "calories": 210, "description": "Batido cremoso rico en 21 vitaminas y minerales.", "image_url": "https://images.unsplash.com/photo-1553787499-6f9133860278?w=800&auto=format&fit=crop&q=80", "customization_options": {"flavors": ["Cookies & Cream", "Chocolate Belga", "Fresa Silvestre", "Vainilla Francesa", "Café Latte"], "toppings": ["Granola", "Chía", "Coco"]}},
            {"name": "Mega Té NRG Guaraná & Antioxidante", "category": "tes_bebidas", "price": 2.50, "protein_grams": 0.0, "calories": 15, "description": "Explosión de energía natural y alerta mental.", "image_url": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=800&auto=format&fit=crop&q=80", "customization_options": {"flavors": ["Frutos Rojos", "Limón", "Durazno"]}},
            {"name": "Herbal Aloe Concentrado (Shot)", "category": "tes_bebidas", "price": 2.00, "protein_grams": 0.0, "calories": 5, "description": "Bebida purificante que desinflama el tracto digestivo.", "image_url": "https://images.unsplash.com/photo-1546173159-315724a31696?w=800&auto=format&fit=crop&q=80", "customization_options": {"flavors": ["Mango", "Mandarina", "Original"]}},
            {"name": "Waffle Proteico Gourmet", "category": "waffles_bowls", "price": 4.50, "protein_grams": 26.0, "calories": 280, "description": "Waffle recién horneado con masa proteica F1.", "image_url": "https://images.unsplash.com/photo-1562376552-0d160a2f238d?w=800&auto=format&fit=crop&q=80", "customization_options": {"flavors": ["Vainilla", "Chocolate"], "toppings": ["Fresas", "Miel Sin Azúcar", "Topping Choco"]}},
            {"name": "Combo Desayuno Saludable 3 Pasos", "category": "combos", "price": 6.50, "protein_grams": 25.0, "calories": 230, "description": "1) Shot de Aloe + 2) Té Energizante + 3) Batido Nutricional F1.", "image_url": "https://images.unsplash.com/photo-1494859802809-d069c3b71a8a?w=800&auto=format&fit=crop&q=80", "customization_options": {"flavors": ["Batido a Elección", "Sabor Aloe", "Sabor Té"]}},
            {"name": "Chupapanzas Herbal Quema-Grasa", "category": "tes_bebidas", "price": 3.50, "protein_grams": 5.0, "calories": 25, "description": "Té + Aloe + Fibra de Manzana para aplanar el abdomen.", "image_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=800&auto=format&fit=crop&q=80", "customization_options": {"flavors": ["Manzana Cítrica", "Mango Guaraná"]}},
            {"name": "Protein Bowl de Avena & Semillas", "category": "waffles_bowls", "price": 4.00, "protein_grams": 22.0, "calories": 250, "description": "Bowl energizante con avena integral, chía y fruta fresca.", "image_url": "https://images.unsplash.com/photo-1590301157890-4810ed352733?w=800&auto=format&fit=crop&q=80", "customization_options": {"flavors": ["Base Fresa", "Base Chocolate"], "toppings": ["Frutos Rojos", "Mantequilla Maní"]}},
            {"name": "Barra de Proteína Deluxe", "category": "snacks", "price": 2.50, "protein_grams": 10.0, "calories": 140, "description": "Snack crujiente con chocolate oscuro.", "image_url": "https://images.unsplash.com/photo-1622484216850-258055694218?w=800&auto=format&fit=crop&q=80", "customization_options": {"flavors": ["Vainilla Almendra", "Cacahuate"]}}
        ]

        added = 0
        for item in STARTER_MENU:
            if not Product.query.filter_by(distributor_id=distributor.id, name=item['name']).first():
                p = Product(
                    distributor_id=distributor.id,
                    name=item['name'],
                    category=item['category'],
                    price=item['price'],
                    protein_grams=item['protein_grams'],
                    calories=item['calories'],
                    description=item['description'],
                    image_url=item['image_url'],
                    customization_options=item['customization_options'],
                    is_available=True,
                    is_club_menu=True,
                    display_order=added
                )
                db.session.add(p)
                added += 1

        db.session.commit()
        return f"🎉 ¡Listo! Se cargaron {added} recetas y preparaciones típicas de Club de Nutrición. Ya puedes verlas o personalizarlas."

    def list_recent_club_orders(self) -> str:
        """View recent orders placed in the club"""
        db.session.rollback()
        distributor = self._get_distributor()
        if not distributor:
            return "Error: No distributor context found."

        orders = ClubOrder.query.filter_by(distributor_id=distributor.id).order_by(ClubOrder.created_at.desc()).limit(5).all()
        if not orders:
            return "Aún no tienes pedidos registrados en el microsite de tu club."

        lines = [f"🛍️ **Últimos {len(orders)} Pedidos del Club:**"]
        for o in orders:
            item_summary = ", ".join([f"{it.get('quantity', 1)}x {it.get('name')}" for it in (o.items or [])])
            lines.append(f"- #{o.order_number}: **{o.customer_name}** ({o.delivery_type}) • Total: ${o.total:.2f} • Estado: {o.status}\n  Ítems: {item_summary}")

        return "\n".join(lines)

    def get_system_prompt_addition(self) -> str:
        """Prompt instructions for Club management"""
        distributor = self._get_distributor()
        club_name = getattr(distributor, 'club_name', None) or "Club de Nutrición"
        club_address = getattr(distributor, 'club_address', None) or ""

        return (
            f"Tienes acceso completo para gestionar el **Club de Nutrición** del distribuidor ('{club_name}'). "
            f"Dirección registrada: '{club_address}'. "
            f"Puedes ayudar al distribuidor a: "
            f"1) Configurar el nombre, eslogan, horarios de atención, dirección y ubicación GPS de su club usando 'update_club_profile'. "
            f"2) Crear, modificar precios, agregar sabores o eliminar preparaciones (waffles, batidos, mega tés, combos) usando 'create_club_product', 'update_club_product', 'delete_club_product'. "
            f"3) Cargar recetas iniciales con 'seed_default_club_menu'. "
            f"4) Consultar pedidos recientes con 'list_recent_club_orders' y compartir los enlaces de Google Maps y Apple Maps con 'get_club_info'. "
            f"Si el distribuidor te pide cosas como 'Agrega un Waffle de Fresa a 4.50' o 'Cambia el horario a 7am a 1pm', EJECUTA las herramientas correspondientes inmediatamente."
        )
