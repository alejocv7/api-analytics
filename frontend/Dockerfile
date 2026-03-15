# syntax=docker.io/docker/dockerfile:1

FROM node:20-alpine AS base

# ----------------------------------------------------------------------------
# Stage 1: deps — install dependencies (shared by dev and prod)
# ----------------------------------------------------------------------------
FROM base AS deps

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# ----------------------------------------------------------------------------
# Stage 2: dev — development server with hot reload
# ----------------------------------------------------------------------------
FROM base AS dev

WORKDIR /app/frontend

ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/frontend/node_modules ./node_modules
COPY frontend ./

CMD ["npm", "run", "dev"]

# ----------------------------------------------------------------------------
# Stage 3: builder — production build
# ----------------------------------------------------------------------------
FROM base AS builder

WORKDIR /app/frontend

COPY --from=deps /app/frontend/node_modules ./node_modules
COPY frontend ./

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# ----------------------------------------------------------------------------
# Step 2. Production image, copy all the files and run next
# ----------------------------------------------------------------------------
FROM base AS runner

WORKDIR /app/frontend

ENV NEXT_TELEMETRY_DISABLED=1

# Don't run production as root
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs
USER nextjs

COPY --from=builder /app/frontend/public ./public

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/frontend/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/frontend/.next/static ./.next/static

CMD ["node", "server.js"]
