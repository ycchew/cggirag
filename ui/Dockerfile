# Stage 1: Build the application
FROM node:18-alpine AS builder

WORKDIR /app

# Accept build argument for NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_API_URL

# Set environment variable for build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Copy package files
COPY package*.json ./

# Install ALL dependencies (including devDependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Production image
FROM node:18-alpine AS runner

WORKDIR /app

# Set to production
ENV NODE_ENV=production

# Copy package files
COPY package*.json ./

# Install only production dependencies
RUN npm ci --only=production

# Copy built application from builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/pages ./pages
COPY --from=builder /app/styles ./styles

EXPOSE 3000

CMD ["npm", "start"]