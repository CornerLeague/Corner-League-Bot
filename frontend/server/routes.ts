import type { Express, Request, Response } from "express";
import { createServer, type Server } from "http";
import { createProxyMiddleware } from 'http-proxy-middleware';
import type { ClientRequest, IncomingMessage } from 'http';
import { storage } from "./storage";

export async function registerRoutes(app: Express): Promise<Server> {
  // Test route to verify Express is working
  app.get('/test', (req: Request, res: Response) => {
    res.json({ message: 'Express is working' });
  });

  // Manual proxy for API requests to the backend server
  console.log('Setting up manual proxy: /api -> http://localhost:8000');
  app.use('/api/*', async (req: Request, res: Response) => {
    try {
      const backendUrl = `http://localhost:8000${req.originalUrl}`;
      console.log(`[PROXY] ${req.method} ${req.originalUrl} -> ${backendUrl}`);
      
      const headers: Record<string, string> = {};
        
        // Copy relevant headers from the request, excluding problematic ones
        const excludeHeaders = ['content-length', 'host', 'connection', 'keep-alive'];
        Object.entries(req.headers).forEach(([key, value]) => {
          if (typeof value === 'string' && !excludeHeaders.includes(key.toLowerCase())) {
            headers[key] = value;
          }
        });
        
        console.log(`[PROXY] Request headers:`, headers);
        console.log(`[PROXY] Request body:`, req.body);
       
       // Prepare the body - send as parsed JSON object
        let body: any;
        if (req.method !== 'GET' && req.body) {
          // req.body is already parsed by Express, send it as-is
          body = req.body;
          headers['Content-Type'] = 'application/json';
          console.log(`[PROXY] Request body:`, req.body);
        }
       
       const response = await fetch(backendUrl, {
           method: req.method,
           headers,
           body: body ? JSON.stringify(body) : undefined,
         });
      
      // Handle both JSON and non-JSON responses
      let data;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = { message: await response.text() };
      }
      
      console.log(`[PROXY] Response status: ${response.status}, data:`, data);
      res.status(response.status).json(data);
    } catch (error) {
      console.error('[PROXY ERROR]', error);
      res.status(500).json({ error: 'Proxy error' });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
