#!/bin/bash

# 创建.env文件
echo "CONFIG_PASSWORD=a" > .env
echo "BOTS_PATH=/backend-api" >> .env

# 停止可能冲突的容器
docker compose down
docker compose -f docker-compose.dev.yml down

# 拉取必要的镜像
docker pull hummingbot/dashboard:latest
docker pull hummingbot/backend-api:latest
docker pull emqx:5

# 启动开发环境
docker compose -f docker-compose.dev.yml up -d

echo "开发环境启动成功！"
echo "Dashboard: http://localhost:8501"
echo "Backend API: http://localhost:8000/docs"
echo "EMQX Dashboard: http://localhost:18083 (admin/public)" 