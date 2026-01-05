#foodgram/infra/nginx/Dockerfile
FROM nginx:1.25.4-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
CMD ["sh", "-c", "until [ -f /usr/share/nginx/html/index.html ]; do echo 'Waiting for frontend build...'; sleep 0.2; done; nginx -g 'daemon off;'"]
