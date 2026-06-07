export default function PublicLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex min-h-screen flex-col bg-muted/30">
            <main className="flex-1">
                {children}
            </main>
            <footer className="py-6 flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <div className="w-5 h-5 shrink-0">
                    <img src="/logo.png" alt="Enpi AI" className="w-full h-full object-contain" />
                </div>
                <span>Powered by <span className="font-semibold text-primary">EnpiAI</span></span>
            </footer>
        </div>
    );
}
