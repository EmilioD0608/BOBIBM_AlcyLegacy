<img width="6912" height="3456" alt="Copia de Blue Coming Soon Banner Landscape" src="https://github.com/user-attachments/assets/4888c13c-262d-4639-aa30-956db7274639" />

<div align="center">

# 🛡️ Alcy Legacy

### Legacy Guardian

**Analyze first. Refactor safely.**

Plataforma para el **análisis y refactorización segura de código legado mediante Inteligencia Artificial**.

Legacy Guardian analiza el riesgo antes de que **BOB** genere una propuesta de refactorización.

</div>

---

## 📌 Descripción

**Alcy Legacy** introduce una capa de seguridad entre el código legado y la Inteligencia Artificial.

En lugar de enviar directamente el código a una IA para modificarlo, **Legacy Guardian** analiza previamente factores como:

- Dependencias del código
- Cobertura de pruebas
- Antigüedad
- Posibles bloqueadores
- Nivel general de riesgo

Como resultado se obtiene un **Risk Score de 0 a 100**, que proporciona contexto antes de delegar la modificación a **BOB**.

### Flujo principal

```text
Código → Legacy Guardian → Análisis de riesgo → BOB → Refactorización → Revisión
```

BOB puede generar **código refactorizado, diff, resumen de cambios y tests propuestos**.

> [!NOTE]
> Los tests son generados por BOB, pero no se consideran ejecutados automáticamente.

---

## 🏗️ Arquitectura

El proyecto está dividido en un **Frontend** y dos APIs independientes:

```text
┌───────────────────────────────┐
│           FRONTEND            │
│    HTML • CSS • JavaScript    │
│                               │
│        Legacy Guardian        │
└───────────────┬───────────────┘
                │ HTTP
                ▼
┌───────────────────────────────┐
│        BACKEND GENERAL        │
│ Node.js • TypeScript • Express│
│                               │
│  Auth • Jobs • GitHub • DB    │
└───────────────┬───────────────┘
                │ API interna
                ▼
┌───────────────────────────────┐
│        BACKEND IA — BOB       │
│       Python • FastAPI        │
│                               │
│   Analyze • Refactor • Diff   │
└───────────────────────────────┘
```

### 🔌 APIs

| Servicio | URL local | Función |
|---|---|---|
| **Backend General** | `http://localhost:3000/api/v1` | API utilizada por el Frontend |
| **Backend IA — BOB** | `http://127.0.0.1:8000` | Análisis y refactorización |

El flujo de comunicación siempre es:

```text
Frontend → Backend General → BOB
```

El **Frontend no consume directamente la API de BOB**.

La comunicación interna entre ambas APIs está protegida mediante `X-Internal-Secret`.

### Endpoints principales de BOB

```http
GET  /internal/v1/health
POST /internal/v1/analyze
POST /internal/v1/refactor
```

---

## 🛡️ Legacy Guardian

Legacy Guardian funciona como un **checkpoint previo a la refactorización**.

```text
                  ┌─────────────────┐
                  │  Código legado  │
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │ Legacy Guardian │
                  └────────┬────────┘
                           ↓
             Risk Score + Bloqueadores
                           ↓
                  ┌─────────────────┐
                  │       BOB       │
                  └────────┬────────┘
                           ↓
                     Refactorización
```

El usuario también puede utilizar el modo **A CIEGAS**, donde BOB recibe directamente la solicitud de modificación sin presentar previamente la capa de evaluación de riesgo.

---

## 🐙 Configuración de GitHub

Antes de analizar o refactorizar un proyecto alojado en GitHub, el usuario debe **instalar y autorizar Alcy Legacy en su cuenta de GitHub**.

### 1️⃣ Instalar Alcy Legacy

Instala la aplicación desde:

👉 [Instalar Alcy Legacy en GitHub](https://github.com/apps/alcy-legacy/installations/new?utm_source)

Durante la instalación, selecciona tu cuenta de GitHub y concede acceso a los repositorios necesarios.

> [!IMPORTANT]
> Para utilizar correctamente funciones como la creación de **forks, ramas, commits y Pull Requests**, Alcy Legacy debe estar instalada en la cuenta de GitHub del usuario.

### 2️⃣ Conectar GitHub

Después de instalar la aplicación:

1. Inicia sesión en Alcy Legacy.
2. Selecciona **Conectar GitHub**.
3. Autoriza la aplicación cuando GitHub lo solicite.
4. Regresa a Alcy Legacy.

El flujo queda de la siguiente manera:

```text
Instalar GitHub App
        ↓
Autorizar cuenta
        ↓
Conectar GitHub
        ↓
Seleccionar repositorio
        ↓
Legacy Guardian
        ↓
BOB
        ↓
Fork / Rama / Commit
        ↓
Pull Request
```

> [!NOTE]
> **Instalar** y **autorizar** la aplicación son procesos diferentes. La autorización permite conectar la identidad del usuario, mientras que la instalación proporciona acceso a los repositorios autorizados.

---

## 📂 Formas de uso

Alcy Legacy permite trabajar con:

| Modo | Descripción |
|---|---|
| 🧪 **Demo** | Código de demostración incluido en la aplicación |
| 📄 **Archivo** | Análisis de un archivo local |
| 📁 **Carpeta** | Análisis de archivos de un proyecto local |
| 🐙 **GitHub** | Análisis y refactorización de proyectos alojados en GitHub |

### Código local

```text
Archivo / Carpeta
       ↓
Legacy Guardian
       ↓
      BOB
       ↓
Código refactorizado
       ↓
    Descarga
```

### Proyecto GitHub

```text
Repositorio
    ↓
Legacy Guardian
    ↓
Análisis
    ↓
BOB
    ↓
Refactorización
    ↓
Fork / Rama
    ↓
Commit
    ↓
Pull Request
```

Alcy Legacy utiliza una **GitHub App junto con GitHub OAuth** para conectar la cuenta del usuario y gestionar las operaciones autorizadas sobre repositorios.

Cuando se trabaja con un repositorio externo, el sistema puede crear un **fork**, generar una rama con los cambios y preparar un Pull Request hacia el repositorio original.

Si GitHub requiere confirmación adicional, el usuario puede continuar el proceso directamente desde GitHub.

---

## 🧩 Stack tecnológico

| Componente | Tecnologías |
|---|---|
| 🌐 **Frontend** | HTML, CSS, JavaScript |
| ⚙️ **Backend General** | Node.js, TypeScript, Express |
| 🧠 **Backend IA** | Python, FastAPI, BOB |
| 🗄️ **Base de datos** | PostgreSQL |
| 🔐 **Autenticación** | JWT, Google Authentication |
| 🐙 **Integración** | GitHub App, GitHub OAuth / GitHub API |

---

## ⚙️ Instalación

### 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/EmilioD0608/BOBIBM_AlcyLegacy.git
cd BOBIBM_AlcyLegacy/BOBIBM_AlcyLegacy-main
```

### 2️⃣ Backend IA — BOB

Se recomienda utilizar **Python 3.10**.

```bash
cd backend/backend_ai

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

Configura el archivo `.env` tomando como referencia `.env.example`.

Luego inicia BOB:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Disponible en:

```text
http://127.0.0.1:8000
```

Documentación Swagger:

```text
http://127.0.0.1:8000/docs
```

---

### 3️⃣ Backend General

Instala las dependencias:

```bash
npm install
```

Configura las variables de entorno:

```env
DB_HOST=
DB_PORT=
DB_USER=
DB_PASSWORD=
DB_NAME=

JWT_SECRET=

BOB_AI_URL=http://localhost:8000
BOB_INTERNAL_SECRET=

GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_CALLBACK_URL=
GITHUB_TOKEN_ENCRYPTION_KEY=
```

Ejecuta el servidor:

```bash
npm run dev
```

El Backend General estará disponible en:

```text
http://localhost:3000
```

---

### 4️⃣ Frontend

El frontend debe utilizar la siguiente URL como API principal:

```text
http://localhost:3000/api/v1
```

El orden recomendado para iniciar el proyecto es:

```text
1. 🧠 Backend IA — BOB       → :8000
2. ⚙️ Backend General        → :3000
3. 🌐 Frontend
```

---

## 🔐 Seguridad

> [!IMPORTANT]
> Los archivos `.env` **no deben subirse al repositorio**.

No publiques contraseñas, tokens, API Keys ni secretos como:

```text
DB_PASSWORD
JWT_SECRET
BOB_INTERNAL_SECRET
GITHUB_CLIENT_SECRET
GITHUB_TOKEN_ENCRYPTION_KEY
```

Utiliza los archivos `.env.example` como referencia para configurar cada entorno.

---

## 🎯 Objetivo

Alcy Legacy propone cambiar el flujo tradicional:

```text
❌ Código → IA → Modificación
```

por un proceso con análisis previo:

```text
✅ Código → Legacy Guardian → Análisis → BOB → Refactorización → Revisión
```

El objetivo es proporcionar al desarrollador **información sobre el riesgo antes de incorporar una modificación generada mediante IA**.

---

<div align="center">

## 🛡️ Alcy Legacy

**Analyze first. Refactor safely.**

*Legacy Guardian + BOB*

</div>

