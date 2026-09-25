# 🚀 Alcy Legacy — Frontend (React + TypeScript + Tailwind CSS)

Este es el frontend oficial del **Skill Alcy Legacy** de **IBM Bob**, desarrollado para el **IBM Bob 2.0 Hackathon**.

## 🛡️ Seguridad e Integración de Backend

El frontend cuenta con:
- **Encabezados HTTP de Seguridad**: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, `CSP`.
- **Limpieza y Desinfección de Entradas**: Protección anti-XSS al pegar código o ingresar URLs de GitHub.
- **Cliente API Centralizado (`src/services/api.ts`)**: Integrado con soporte de Bearer tokens, manejo de errores y fallback transparente si el servidor backend no responde.

Para conectar el backend de Python (`backend/analyzer`), consulta la guía completa:
📄 **[BACKEND_INTEGRATION.md](../BACKEND_INTEGRATION.md)**

---

## 💻 Desarrollo Local

En la carpeta `frontend/`:

1. Instalar dependencias:
   ```bash
   npm install
   ```

2. Configurar variables de entorno (opcional):
   ```bash
   cp .env.example .env
   ```

3. Iniciar servidor de desarrollo:
   ```bash
   npm run dev
   ```

---

## 📦 Compilación para Producción (Netlify)

Para compilar el proyecto y generar el bundle en `dist/`:

```bash
npm run build
```

Netlify detectará automáticamente el archivo `netlify.toml` ubicado en la raíz del proyecto.
