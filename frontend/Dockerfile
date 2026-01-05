# foodgram/frontend/Dockerfile
# foodgram/frontend/Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app

COPY package.json yarn.lock ./
RUN corepack enable && corepack prepare yarn@1.22.22 --activate
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build

FROM alpine:3.20
RUN apk add --no-cache ca-certificates
COPY --from=builder /app/build /build
CMD ["sh", "-c", "rm -rf /frontend_build/* && cp -r /build/. /frontend_build/"]
