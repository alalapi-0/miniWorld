const TILE_COLOR_FALLBACK = {
  GRASS: "#3b8c4c",
  ROAD: "#9aa3ab",
  WATER: "#2a6df2",
  SOIL: "#8c5b3f",
  TREE: "#1f4d25",
  HOUSE_BASE: "#c77232",
};

const COLLISION_TILES = new Set(["WATER", "HOUSE_BASE"]);
const DEFAULT_TILE_SIZE = 32;
const MOVE_ANIMATION_MS = 180;

async function loadJSON(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`请求 ${url} 失败: ${response.status}`);
  }
  return response.json();
}

async function loadImage(url) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error(`无法加载图片: ${url}`));
    image.src = url;
  });
}

function createFrameSets(sheet) {
  const frameWidth = Math.floor(sheet.width / 3);
  const frameHeight = sheet.height;
  return {
    down: [{ sx: 0, sy: 0, sw: frameWidth, sh: frameHeight }],
    left: [{ sx: frameWidth, sy: 0, sw: frameWidth, sh: frameHeight }],
    up: [{ sx: frameWidth * 2, sy: 0, sw: frameWidth, sh: frameHeight }],
    right: [
      {
        sx: frameWidth,
        sy: 0,
        sw: frameWidth,
        sh: frameHeight,
        flipX: true,
      },
    ],
  };
}

function createColor(tile) {
  if (tile in TILE_COLOR_FALLBACK) {
    return TILE_COLOR_FALLBACK[tile];
  }
  let hash = 0;
  for (let i = 0; i < tile.length; i += 1) {
    hash = (hash * 31 + tile.charCodeAt(i)) & 0xffffffff;
  }
  const r = (hash & 0xff0000) >> 16;
  const g = (hash & 0x00ff00) >> 8;
  const b = hash & 0x0000ff;
  return `rgb(${r % 255}, ${g % 255}, ${b % 255})`;
}

function drawMap(ctx, chunk, tileSize) {
  const { grid, size } = chunk;
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const cell = grid[y][x];
      const baseColor = createColor(cell.base);
      ctx.fillStyle = baseColor;
      ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
      if (cell.deco) {
        ctx.fillStyle = createColor(cell.deco);
        const inset = tileSize * 0.2;
        ctx.fillRect(
          x * tileSize + inset,
          y * tileSize + inset,
          tileSize - inset * 2,
          tileSize - inset * 2,
        );
      }
    }
  }
}

function drawPlayer(ctx, sprite, frames, player, tileSize) {
  const frameSet = frames[player.direction];
  const frame = frameSet[player.frameIndex % frameSet.length];
  const screenX = player.x * tileSize + tileSize / 2;
  const screenY = player.y * tileSize + tileSize / 2;
  const drawWidth = tileSize;
  const drawHeight = tileSize * 1.2;
  ctx.save();
  if (frame.flipX) {
    ctx.translate(screenX, screenY);
    ctx.scale(-1, 1);
    ctx.translate(-screenX, -screenY);
  }
  ctx.drawImage(
    sprite,
    frame.sx,
    frame.sy,
    frame.sw,
    frame.sh,
    screenX - drawWidth / 2,
    screenY - drawHeight,
    drawWidth,
    drawHeight,
  );
  ctx.restore();
}

function isBlocked(chunk, x, y) {
  if (x < 0 || y < 0 || x >= chunk.size || y >= chunk.size) {
    return true;
  }
  const cell = chunk.grid[y][x];
  if (COLLISION_TILES.has(cell.base)) {
    return true;
  }
  if (cell.deco && COLLISION_TILES.has(cell.deco)) {
    return true;
  }
  return false;
}

function findSpawn(chunk) {
  const center = Math.floor(chunk.size / 2);
  const radius = Math.max(center, 1);
  for (let r = 0; r <= radius; r += 1) {
    for (let dy = -r; dy <= r; dy += 1) {
      for (let dx = -r; dx <= r; dx += 1) {
        const x = center + dx;
        const y = center + dy;
        if (!isBlocked(chunk, x, y)) {
          return { x, y };
        }
      }
    }
  }
  return { x: 0, y: 0 };
}

function setupControls(state) {
  const moveMap = new Map([
    ["ArrowUp", { dx: 0, dy: -1, direction: "up" }],
    ["KeyW", { dx: 0, dy: -1, direction: "up" }],
    ["ArrowDown", { dx: 0, dy: 1, direction: "down" }],
    ["KeyS", { dx: 0, dy: 1, direction: "down" }],
    ["ArrowLeft", { dx: -1, dy: 0, direction: "left" }],
    ["KeyA", { dx: -1, dy: 0, direction: "left" }],
    ["ArrowRight", { dx: 1, dy: 0, direction: "right" }],
    ["KeyD", { dx: 1, dy: 0, direction: "right" }],
  ]);

  window.addEventListener("keydown", (event) => {
    const move = moveMap.get(event.code);
    if (!move) {
      return;
    }
    event.preventDefault();
    const { chunk, player } = state;
    player.direction = move.direction;
    const targetX = player.x + move.dx;
    const targetY = player.y + move.dy;
    if (isBlocked(chunk, targetX, targetY)) {
      player.isMoving = false;
      player.frameIndex = 0;
      return;
    }
    player.x = targetX;
    player.y = targetY;
    player.isMoving = true;
    player.frameIndex = (player.frameIndex + 1) % state.frames[player.direction].length;
    player.frameTimer = 0;
  });

  window.addEventListener("keyup", (event) => {
    if (moveMap.has(event.code)) {
      state.player.isMoving = false;
      state.player.frameTimer = 0;
      state.player.frameIndex = 0;
    }
  });
}

function updatePlayerAnimation(state, delta) {
  const { player, frames } = state;
  if (!player.isMoving) {
    player.frameIndex = 0;
    return;
  }
  player.frameTimer += delta;
  if (player.frameTimer >= MOVE_ANIMATION_MS) {
    player.frameTimer = 0;
    player.frameIndex = (player.frameIndex + 1) % frames[player.direction].length;
  }
}

function render(state) {
  const { ctx, chunk, tileSize, sprite, frames, player } = state;
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  drawMap(ctx, chunk, tileSize);
  drawPlayer(ctx, sprite, frames, player, tileSize);
}

async function initExplorer() {
  const canvas = document.getElementById("world-canvas");
  const ctx = canvas.getContext("2d");
  let tileSize = DEFAULT_TILE_SIZE;
  try {
    const binding = await loadJSON("../assets/mapping/tileset_binding.json");
    if (binding.tile_size) {
      tileSize = binding.tile_size;
    }
  } catch (error) {
    console.warn("无法加载 tileset 配置，使用默认尺寸", error);
  }

  const chunk = await loadJSON("/world/chunk?cx=0&cy=0");
  canvas.width = chunk.size * tileSize;
  canvas.height = chunk.size * tileSize;

  const sprite = await loadImage("../assets/sprites/user_character/sheet.png");
  const frames = createFrameSets(sprite);
  const spawn = findSpawn(chunk);

  const state = {
    ctx,
    chunk,
    tileSize,
    sprite,
    frames,
    player: {
      x: spawn.x,
      y: spawn.y,
      direction: "down",
      frameIndex: 0,
      frameTimer: 0,
      isMoving: false,
    },
    lastTime: performance.now(),
  };

  setupControls(state);

  function loop(now) {
    const delta = now - state.lastTime;
    state.lastTime = now;
    updatePlayerAnimation(state, delta);
    render(state);
    requestAnimationFrame(loop);
  }

  requestAnimationFrame(loop);
}

initExplorer().catch((error) => {
  const canvas = document.getElementById("world-canvas");
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#ff4d4f";
  ctx.font = "16px sans-serif";
  ctx.fillText(`加载失败: ${error.message}`, 16, 32);
  console.error(error);
});
