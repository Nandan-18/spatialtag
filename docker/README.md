# Docker Web UI

Browser-based metadata injection for MP4/MOV files.

**Full guide:** [nandan-18.github.io/spatial-media/guide/docker.html](https://nandan-18.github.io/spatial-media/guide/docker.html)

```bash
docker build -t spatial-media-web -f docker/Dockerfile .
docker run -p 5000:5000 -v "$(pwd)/data:/app/uploads" spatial-media-web
```
