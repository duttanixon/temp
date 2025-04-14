from node:22-alpine as builder

WORKDIR /app

# Enable corepack for yarn
RUN corepack enable

# Copy package.json, yarn.lock and .yarnrc.yml
COPY package.json yarn.lock .yarnrc.yml ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy the rest of the application
COPY . .

# Build the Next.js application
RUN yarn build

# Production image
FROM node:22-alpine AS runner

WORKDIR /app

# Enable corepack for yarn
RUN corepack enable

# Copy dependency files from builder stage
COPY --from=builder /app/package.json /app/yarn.lock /app/.yarnrc.yml ./

# Install production dependencies
RUN yarn install --immutable


# Copy built assests and public directory from builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Add a non-root user and set ownership
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs && \
    chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Set production environment
ENV NODE_ENV=production

# Expose port
EXPOSE 3000

# Start the application
CMD ["yarn", "start"]


# Alternative approach: Use nodelinker: node-modules in .yarnrc.yml
# FROM node:22-alpine

# WORKDIR /app

# # Enable corepack for yarn
# RUN corepack enable

# # Copy package.json and yarn.lock
# COPY package.json yarn.lock .yarnrc.yml ./

# # Install dependencies using node-modules linker
# RUN yarn install

# # Copy the rest of the application
# COPY . .

# # Build the application
# RUN yarn build

# # Add a non-root user to run the application
# RUN addgroup --system --gid 1001 nodejs && \
#     adduser --system --uid 1001 nextjs && \
#     chown -R nextjs:nodejs /app

# # Switch to non-root user
# USER nextjs

# # Set production environment
# ENV NODE_ENV=production

# # Expose port
# EXPOSE 3000

# # Start the application
# CMD ["yarn", "start"]
