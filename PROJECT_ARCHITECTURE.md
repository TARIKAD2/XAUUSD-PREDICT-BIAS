# Architecture

Routes call services; services use collectors and Mongo repositories. Collectors validate and normalize external data before persistence. Features and ML use chronological ordering to prevent future-data leakage. The Next.js app uses one centralized API client. Docker uses only relative paths.