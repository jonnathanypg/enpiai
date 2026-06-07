export default function Loading() {
  return (
    <div className="flex h-full w-full items-center justify-center p-8">
      <div className="flex flex-col items-center gap-4">
        <div className="relative h-16 w-16">
          <div className="absolute inset-0 animate-ping rounded-full bg-primary/20" />
          <div className="relative flex h-16 w-16 items-center justify-center rounded-full border-4 border-primary border-t-transparent animate-spin" />
        </div>
        <div className="flex flex-col items-center">
          <p className="text-lg font-semibold animate-pulse bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Cargando experiencia Enpi AI...
          </p>
          <p className="text-sm text-muted-foreground italic">Preparando tus herramientas de éxito</p>
        </div>
      </div>
    </div>
  );
}
