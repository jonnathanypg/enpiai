export default function AuthLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-background via-muted/30 to-background p-4">
            <div className="mb-8 flex flex-col items-center gap-2">
                <div className="w-16 h-16 shrink-0">
                    <img src="/logo.png" alt="Enpi AI" className="w-full h-full object-contain" />
                </div>
                <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-br from-primary to-secondary bg-clip-text text-transparent">
                    Enpi AI
                </h1>
            </div>
            <div className="w-full max-w-md">{children}</div>
        </div>
    );
}
