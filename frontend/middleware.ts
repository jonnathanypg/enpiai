import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    const token = request.cookies.get('access_token')?.value;
    const { pathname } = request.nextUrl;

    // Paths that require authentication
    const protectedPaths = [
        '/dashboard', '/agents', '/settings', '/subscribe',
        '/channels', '/wellness', '/documents', '/contacts',
        '/coach', '/admin',
    ];
    const isProtected = protectedPaths.some((path) => pathname.startsWith(path));

    // Paths that are only for non-authenticated users
    const authPaths = ['/login', '/register'];
    const isAuthPath = authPaths.some((path) => pathname.startsWith(path));

    if (isProtected && !token) {
        return NextResponse.redirect(new URL('/login', request.url));
    }

    if (isAuthPath && token) {
        return NextResponse.redirect(new URL('/dashboard', request.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: [
        '/dashboard/:path*',
        '/agents/:path*',
        '/settings/:path*',
        '/subscribe/:path*',
        '/channels/:path*',
        '/wellness/:path*',
        '/documents/:path*',
        '/contacts/:path*',
        '/coach/:path*',
        '/admin/:path*',
        '/login',
        '/register',
    ],
};
