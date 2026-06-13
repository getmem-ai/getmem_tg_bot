# syntax=docker/dockerfile:1

# ---- deps: install production + dev deps for the build ----
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
# Use npm ci when a lockfile exists, otherwise fall back to npm install.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# ---- build: compile the Next.js standalone output ----
FROM node:22-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
# NEXT_PUBLIC_* vars are inlined into the bundle at build time, so the API base
# URL must be provided here (compose passes it as a build arg).
ARG NEXT_PUBLIC_API_BASE=/api
ENV NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ---- runner: minimal runtime image ----
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Run as a non-root user.
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

COPY --from=build /app/public ./public
COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
