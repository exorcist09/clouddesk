FROM oven/bun:latest AS builder

WORKDIR /app

# Copy dependency definitions
COPY package.json bun.lock ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy app code
COPY next.config.ts tsconfig.json ./
COPY public ./public
COPY src ./src

# Environment for Next.js build
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Build Next.js application
RUN bun run build

# Production runner stage
FROM oven/bun:latest AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["bun", "run", "start"]