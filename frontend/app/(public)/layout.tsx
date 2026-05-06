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
            <footer className="py-6 text-center text-sm text-muted-foreground">
                Powered by <span className="font-semibold text-primary">EnpiAI</span>
            </footer>
        </div>
    );
}
