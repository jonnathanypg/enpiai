export default function AuthLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-background via-muted/30 to-background p-4">
            <div className="mb-8 flex flex-col items-center">
                <img src="/favicon-enpiai-ligth.png" alt="Enpi AI" className="h-14 w-auto object-contain dark:hidden" />
                <img src="/favicon-enpiai-dark.png" alt="Enpi AI" className="h-14 w-auto object-contain hidden dark:block" />
            </div>
            <div className="w-full max-w-md">{children}</div>
        </div>
    );
}
