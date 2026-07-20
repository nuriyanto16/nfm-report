FROM node:20-slim AS build
WORKDIR /app
# baseURL harus di-bake saat build (untuk path aset). apiBase bisa di-bake juga
# dan tetap dapat di-override saat runtime via NUXT_PUBLIC_API_BASE.
ARG NUXT_APP_BASE_URL=/
ARG NUXT_PUBLIC_API_BASE=
ENV NUXT_APP_BASE_URL=$NUXT_APP_BASE_URL \
    NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=build /app/.output ./.output
ENV NITRO_HOST=0.0.0.0 NITRO_PORT=3000
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
