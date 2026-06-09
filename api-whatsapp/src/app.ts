import "dotenv/config"
import express from "express"
import cors from "cors"
import routes from "./infrastructure/router"

const port = process.env.PORT || 3001
const app = express()

// CORS restricted to backend
app.use(cors({ origin: process.env.BACKEND_URL || 'http://localhost:5000' }))
app.use(express.json())

// Healthcheck
app.get('/health', (_, res) => res.json({ status: 'ok' }))

// Simple Authentication via API Secret
app.use((req, res, next) => {
    const secret = req.headers['x-api-secret'];
    if (secret && process.env.API_SECRET && secret !== process.env.API_SECRET) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
})

app.use(`/`, routes)

// Global Error handler
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
    console.error('[GLOBAL ERROR]', err)
    res.status(500).json({ error: 'Internal server error' })
})

// Prevent crash from uncaught exceptions
process.on('uncaughtException', (err) => console.error('[UNCAUGHT]', err))
process.on('unhandledRejection', (reason) => console.error('[UNHANDLED]', reason))

app.listen(port, () => console.log(`WhatsApp API ready on port ${port}`))