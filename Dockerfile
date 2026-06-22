FROM node:20-alpine AS base

# Dependencies (prod only)
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
COPY prisma ./prisma/
RUN npm install --omit=dev && npx prisma generate

# Build
FROM base AS builder
WORKDIR /app
COPY package.json package-lock.json ./
COPY prisma ./prisma/
RUN npm install
COPY . .
RUN npx prisma generate && npm run build

# Production
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nestjs && \
    adduser --system --uid 1001 nestjs

COPY --from=builder /app/dist ./dist
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/prisma ./prisma
COPY package.json ./

RUN mkdir -p /app/uploads && chown nestjs:nestjs /app/uploads

USER nestjs
EXPOSE 3000
CMD ["node", "dist/main"]
