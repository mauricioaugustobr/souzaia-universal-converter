// SOUZAIA Universal Converter - Frontend Application Engine

let state = {
  queue: [], // List of { file_id, original_name, temp_path, info, targetFormat, options, status, progress, message, jobId, result }
  formats: {},
  activeFilter: 'all',
  isConvertingAll: false
};

// Category Icons (SVG strings)
const ICONS = {
  video: `<svg class="w-6 h-6 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>`,
  audio: `<svg class="w-6 h-6 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/></svg>`,
  image: `<svg class="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>`,
  document: `<svg class="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>`,
  unknown: `<svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>`
};

document.addEventListener('DOMContentLoaded', () => {
  initDropzone();
  initPasteListener();
  loadFormats();
  setupFilterTabs();
  setupBatchControls();
});

async function loadFormats() {
  try {
    const res = await fetch('/api/formats');
    state.formats = await res.json();
  } catch (err) {
    console.error('Erro ao carregar matriz de formatos:', err);
  }
}

function initDropzone() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');

  dropzone.addEventListener('click', () => fileInput.click());

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFilesUpload(files);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFilesUpload(e.target.files);
      e.target.value = ''; // Reset for re-selection
    }
  });
}

function initPasteListener() {
  window.addEventListener('paste', (e) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    const files = [];
    for (let i = 0; i < items.length; i++) {
      if (items[i].kind === 'file') {
        const file = items[i].getAsFile();
        if (file) files.push(file);
      }
    }
    if (files.length > 0) {
      handleFilesUpload(files);
    }
  });
}

async function handleFilesUpload(fileList) {
  const formData = new FormData();
  for (let i = 0; i < fileList.length; i++) {
    formData.append('files', fileList[i]);
  }

  // Show upload toast
  showToast(`Enviando ${fileList.length} arquivo(s)...`);

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) throw new Error('Falha no upload');
    const data = await res.json();

    data.files.forEach(item => {
      const suggestedTarget = item.info.target_formats && item.info.target_formats.length > 0 
        ? item.info.target_formats[0] 
        : 'mp4';

      state.queue.push({
        file_id: item.file_id,
        original_name: item.original_name,
        temp_path: item.temp_path,
        info: item.info,
        targetFormat: suggestedTarget,
        options: getDefaultOptions(item.info.category),
        status: 'ready', // 'ready', 'converting', 'completed', 'failed'
        progress: 0,
        message: 'Pronto para converter',
        jobId: null,
        result: null
      });
    });

    renderQueue();
    updateBatchBar();
  } catch (err) {
    showToast(`Erro no upload: ${err.message}`, 'error');
  }
}

function getDefaultOptions(category) {
  if (category === 'video') {
    return { quality: 'high', resolution: 'original', fps: null, audio_bitrate: '320k' };
  } else if (category === 'audio') {
    return { quality: 'high', audio_bitrate: '320k', normalize: false };
  } else if (category === 'image') {
    return { image_quality: 98, dpi: 300, width: null, height: null };
  } else if (category === 'document') {
    return { dpi: 300 };
  }
  return {};
}

function renderQueue() {
  const container = document.getElementById('queueContainer');
  const emptyState = document.getElementById('emptyState');
  const countBadge = document.getElementById('queueCountBadge');

  const filteredQueue = state.queue.filter(item => {
    if (state.activeFilter === 'all') return true;
    return item.info.category === state.activeFilter;
  });

  countBadge.textContent = state.queue.length;

  if (state.queue.length === 0) {
    container.innerHTML = '';
    emptyState.classList.remove('hidden');
    return;
  }

  emptyState.classList.add('hidden');
  container.innerHTML = filteredQueue.map((item, index) => renderQueueItem(item, index)).join('');
}

function renderQueueItem(item, index) {
  const cat = item.info.category || 'unknown';
  const icon = ICONS[cat] || ICONS.unknown;
  const targets = item.info.target_formats || ['mp4', 'mp3', 'png', 'pdf'];

  // Badges metadata
  let metaDetails = [];
  if (item.info.details) {
    const d = item.info.details;
    if (d.resolution) metaDetails.push(d.resolution);
    if (d.duration_formatted) metaDetails.push(d.duration_formatted);
    if (d.pages) metaDetails.push(`${d.pages} páginas`);
    if (d.fps) metaDetails.push(`${d.fps} fps`);
  }

  const badgeClass = `badge-${cat}`;

  return `
    <div class="glass-panel p-5 transition-all duration-300 hover:border-indigo-500/30" id="item-${item.file_id}">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        <!-- Left: Icon & Info -->
        <div class="flex items-start gap-4 min-w-0 flex-1">
          <div class="p-3 rounded-xl bg-slate-800/80 border border-slate-700/50 flex-shrink-0">
            ${icon}
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 flex-wrap">
              <h4 class="font-semibold text-slate-100 truncate text-base" title="${item.original_name}">
                ${item.original_name}
              </h4>
              <span class="text-xs px-2 py-0.5 rounded-full font-medium uppercase ${badgeClass}">
                ${cat}
              </span>
            </div>
            <div class="flex items-center gap-3 text-xs text-slate-400 mt-1 flex-wrap">
              <span>${item.info.size_formatted}</span>
              ${metaDetails.map(m => `<span>• ${m}</span>`).join('')}
            </div>
          </div>
        </div>

        <!-- Middle: Target Format Selector -->
        <div class="flex items-center gap-3">
          <span class="text-xs text-slate-400 font-medium">Converter para:</span>
          <select 
            class="glass-input text-sm font-semibold uppercase bg-slate-900 border border-slate-700 text-indigo-300 cursor-pointer px-3 py-1.5 rounded-lg"
            onchange="updateTargetFormat('${item.file_id}', this.value)"
            ${item.status === 'converting' ? 'disabled' : ''}
          >
            ${targets.map(t => `
              <option value="${t}" ${t === item.targetFormat ? 'selected' : ''}>
                .${t.toUpperCase()}
              </option>
            `).join('')}
          </select>

          <!-- Advanced Options Button -->
          <button 
            onclick="toggleOptions('${item.file_id}')"
            class="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-800/80 rounded-lg transition"
            title="Configurações Avançadas"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          </button>
        </div>

        <!-- Right: Actions -->
        <div class="flex items-center gap-2">
          ${item.status === 'completed' ? `
            <a 
              href="/api/download/${item.jobId}" 
              download
              class="btn-primary text-xs py-2 px-3 bg-emerald-600 hover:bg-emerald-500 shadow-emerald-500/20"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
              Baixar (${item.result?.size_formatted || ''})
            </a>
          ` : item.status === 'converting' ? `
            <button disabled class="btn-secondary text-xs opacity-60 cursor-not-allowed">
              <svg class="animate-spin w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
              Convertendo...
            </button>
          ` : `
            <button 
              onclick="startConversion('${item.file_id}')"
              class="btn-primary text-xs py-2 px-3"
            >
              Converter
            </button>
          `}

          <button 
            onclick="removeFromQueue('${item.file_id}')"
            class="p-2 text-slate-500 hover:text-rose-400 rounded-lg transition"
            title="Remover"
            ${item.status === 'converting' ? 'disabled' : ''}
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          </button>
        </div>

      </div>

      <!-- Progress Section (when active or completed) -->
      ${item.status === 'converting' || item.status === 'completed' || item.status === 'failed' ? `
        <div class="mt-4 pt-3 border-t border-slate-800">
          <div class="flex justify-between text-xs mb-1.5">
            <span class="${item.status === 'failed' ? 'text-rose-400' : 'text-slate-300'} font-medium">
              ${item.message}
            </span>
            <span class="font-bold text-indigo-300">${item.progress.toFixed(0)}%</span>
          </div>
          <div class="progress-container">
            <div 
              class="progress-fill ${item.status === 'completed' ? 'bg-emerald-500' : item.status === 'failed' ? 'bg-rose-500' : ''}" 
              style="width: ${item.progress}%"
            ></div>
          </div>
        </div>
      ` : ''}

      <!-- Collapsible Advanced Options -->
      <div id="options-${item.file_id}" class="hidden mt-4 pt-4 border-t border-slate-800/80 bg-slate-900/40 -mx-5 -mb-5 p-5 rounded-b-xl text-xs">
        <h5 class="font-semibold text-slate-300 mb-3 flex items-center gap-1.5">
          <svg class="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg>
          Ajustes de Qualidade e Formato
        </h5>
        ${renderOptionsPanel(item)}
      </div>

    </div>
  `;
}

function renderOptionsPanel(item) {
  const cat = item.info.category;
  if (cat === 'video') {
    return `
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-slate-400 mb-1">Qualidade de Codificação:</label>
          <select 
            class="glass-input w-full"
            onchange="updateOption('${item.file_id}', 'quality', this.value)"
          >
            <option value="ultra" ${item.options.quality === 'ultra' ? 'selected' : ''}>Ultra (Sem Perdas Visuais)</option>
            <option value="high" ${item.options.quality === 'high' ? 'selected' : ''}>Alta Qualidade (CRF 18 - Recomendado)</option>
            <option value="balanced" ${item.options.quality === 'balanced' ? 'selected' : ''}>Balanceado (CRF 22)</option>
            <option value="web" ${item.options.quality === 'web' ? 'selected' : ''}>Otimizado para Web (CRF 26)</option>
          </select>
        </div>
        <div>
          <label class="block text-slate-400 mb-1">Resolução:</label>
          <select 
            class="glass-input w-full"
            onchange="updateOption('${item.file_id}', 'resolution', this.value)"
          >
            <option value="original" ${item.options.resolution === 'original' ? 'selected' : ''}>Manter Original</option>
            <option value="4k" ${item.options.resolution === '4k' ? 'selected' : ''}>4K UHD (3840x2160)</option>
            <option value="1080p" ${item.options.resolution === '1080p' ? 'selected' : ''}>Full HD (1080p)</option>
            <option value="720p" ${item.options.resolution === '720p' ? 'selected' : ''}>HD (720p)</option>
            <option value="480p" ${item.options.resolution === '480p' ? 'selected' : ''}>SD (480p)</option>
          </select>
        </div>
        <div>
          <label class="block text-slate-400 mb-1">Bitrate de Áudio:</label>
          <select 
            class="glass-input w-full"
            onchange="updateOption('${item.file_id}', 'audio_bitrate', this.value)"
          >
            <option value="320k" ${item.options.audio_bitrate === '320k' ? 'selected' : ''}>320 kbps (Máxima Fidelidade)</option>
            <option value="256k" ${item.options.audio_bitrate === '256k' ? 'selected' : ''}>256 kbps</option>
            <option value="192k" ${item.options.audio_bitrate === '192k' ? 'selected' : ''}>192 kbps</option>
          </select>
        </div>
      </div>
    `;
  } else if (cat === 'audio') {
    return `
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-slate-400 mb-1">Taxa de Bits (Bitrate):</label>
          <select 
            class="glass-input w-full"
            onchange="updateOption('${item.file_id}', 'audio_bitrate', this.value)"
          >
            <option value="320k" ${item.options.audio_bitrate === '320k' ? 'selected' : ''}>320 kbps (Qualidade de Estúdio)</option>
            <option value="256k" ${item.options.audio_bitrate === '256k' ? 'selected' : ''}>256 kbps</option>
            <option value="192k" ${item.options.audio_bitrate === '192k' ? 'selected' : ''}>192 kbps</option>
            <option value="128k" ${item.options.audio_bitrate === '128k' ? 'selected' : ''}>128 kbps</option>
          </select>
        </div>
        <div class="flex items-center gap-2 pt-5">
          <input 
            type="checkbox" 
            id="norm-${item.file_id}" 
            class="rounded border-slate-700 bg-slate-900 text-indigo-500 focus:ring-indigo-500"
            ${item.options.normalize ? 'checked' : ''}
            onchange="updateOption('${item.file_id}', 'normalize', this.checked)"
          >
          <label for="norm-${item.file_id}" class="text-slate-300 cursor-pointer">
            Normalizar Volume (Padrão EBU R128 para Streaming)
          </label>
        </div>
      </div>
    `;
  } else if (cat === 'image') {
    return `
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-slate-400 mb-1">Qualidade (1 a 100%):</label>
          <input 
            type="range" 
            min="10" 
            max="100" 
            value="${item.options.image_quality || 98}" 
            class="w-full accent-indigo-500"
            oninput="this.nextElementSibling.value = this.value; updateOption('${item.file_id}', 'image_quality', parseInt(this.value))"
          >
          <output class="text-indigo-400 font-bold ml-1">${item.options.image_quality || 98}%</output>
        </div>
        <div>
          <label class="block text-slate-400 mb-1">Densidade DPI (Resolução de Impressão):</label>
          <select 
            class="glass-input w-full"
            onchange="updateOption('${item.file_id}', 'dpi', parseInt(this.value))"
          >
            <option value="300" ${item.options.dpi === 300 ? 'selected' : ''}>300 DPI (Qualidade Gráfica de Impressão)</option>
            <option value="150" ${item.options.dpi === 150 ? 'selected' : ''}>150 DPI (Equilibrado)</option>
            <option value="72" ${item.options.dpi === 72 ? 'selected' : ''}>72 DPI (Tela / Web)</option>
          </select>
        </div>
        <div>
          <label class="block text-slate-400 mb-1">Filtro de Reamostragem:</label>
          <input type="text" disabled value="LANCZOS (Máxima Nitidez)" class="glass-input w-full opacity-70">
        </div>
      </div>
    `;
  } else if (cat === 'document') {
    return `
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-slate-400 mb-1">DPI para Imagens Renderizadas:</label>
          <select 
            class="glass-input w-full"
            onchange="updateOption('${item.file_id}', 'dpi', parseInt(this.value))"
          >
            <option value="300" ${item.options.dpi === 300 ? 'selected' : ''}>300 DPI (Ultra-Nítido)</option>
            <option value="150" ${item.options.dpi === 150 ? 'selected' : ''}>150 DPI (Padrão)</option>
          </select>
        </div>
        <div class="pt-5 text-slate-400">
          <p>Formatos como PDF ➔ DOCX preservam títulos, parágrafos e paginação original.</p>
        </div>
      </div>
    `;
  }
  return `<p class="text-slate-400">Opções padrão automáticas aplicadas com máxima qualidade.</p>`;
}

function toggleOptions(fileId) {
  const panel = document.getElementById(`options-${fileId}`);
  if (panel) {
    panel.classList.toggle('hidden');
  }
}

function updateTargetFormat(fileId, target) {
  const item = state.queue.find(q => q.file_id === fileId);
  if (item) {
    item.targetFormat = target;
  }
}

function updateOption(fileId, key, value) {
  const item = state.queue.find(q => q.file_id === fileId);
  if (item) {
    item.options[key] = value;
  }
}

function removeFromQueue(fileId) {
  state.queue = state.queue.filter(q => q.file_id !== fileId);
  renderQueue();
  updateBatchBar();
}

async function startConversion(fileId) {
  const item = state.queue.find(q => q.file_id === fileId);
  if (!item || item.status === 'converting') return;

  item.status = 'converting';
  item.progress = 5;
  item.message = 'Iniciando conversão...';
  renderQueue();

  try {
    const res = await fetch('/api/convert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_id: item.file_id,
        temp_path: item.temp_path,
        target_format: item.targetFormat,
        options: item.options
      })
    });

    if (!res.ok) throw new Error('Não foi possível iniciar a conversão');
    const data = await res.json();
    item.jobId = data.job_id;

    pollProgress(item);
  } catch (err) {
    item.status = 'failed';
    item.message = err.message;
    renderQueue();
  }
}

function pollProgress(item) {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/progress/${item.jobId}`);
      if (!res.ok) throw new Error('Job não encontrado');
      const data = await res.json();

      item.progress = data.progress;
      item.message = data.message;

      if (data.status === 'completed') {
        clearInterval(interval);
        item.status = 'completed';
        item.result = data.result;
        renderQueue();
        updateBatchBar();
        showToast(`"${item.original_name}" convertido para .${item.targetFormat.toUpperCase()}!`, 'success');
      } else if (data.status === 'failed') {
        clearInterval(interval);
        item.status = 'failed';
        item.message = data.error || 'Erro na conversão';
        renderQueue();
        updateBatchBar();
        showToast(`Erro ao converter ${item.original_name}`, 'error');
      } else {
        renderQueue();
      }
    } catch (err) {
      clearInterval(interval);
      item.status = 'failed';
      item.message = err.message;
      renderQueue();
    }
  }, 400);
}

function setupFilterTabs() {
  const tabs = document.querySelectorAll('.filter-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('bg-indigo-600', 'text-white'));
      tabs.forEach(t => t.classList.add('text-slate-400'));
      tab.classList.add('bg-indigo-600', 'text-white');
      tab.classList.remove('text-slate-400');
      state.activeFilter = tab.getAttribute('data-filter');
      renderQueue();
    });
  });
}

function setupBatchControls() {
  const btnConvertAll = document.getElementById('btnConvertAll');
  const btnDownloadZip = document.getElementById('btnDownloadZip');
  const btnClearCompleted = document.getElementById('btnClearCompleted');

  btnConvertAll.addEventListener('click', async () => {
    const readyItems = state.queue.filter(i => i.status === 'ready' || i.status === 'failed');
    if (readyItems.length === 0) return;

    for (const item of readyItems) {
      startConversion(item.file_id);
    }
  });

  btnDownloadZip.addEventListener('click', async () => {
    const completedJobs = state.queue.filter(i => i.status === 'completed' && i.jobId).map(i => i.jobId);
    if (completedJobs.length === 0) return;

    try {
      const res = await fetch('/api/batch-download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_ids: completedJobs })
      });
      if (!res.ok) throw new Error('Falha ao gerar ZIP consolidado');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SOUZAIA_Arquivos_Convertidos.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      showToast(`Erro ao baixar ZIP: ${err.message}`, 'error');
    }
  });

  btnClearCompleted.addEventListener('click', () => {
    state.queue = state.queue.filter(i => i.status !== 'completed');
    renderQueue();
    updateBatchBar();
  });
}

function updateBatchBar() {
  const completedCount = state.queue.filter(i => i.status === 'completed').length;
  const readyCount = state.queue.filter(i => i.status === 'ready' || i.status === 'failed').length;

  const btnConvertAll = document.getElementById('btnConvertAll');
  const btnDownloadZip = document.getElementById('btnDownloadZip');
  const btnClearCompleted = document.getElementById('btnClearCompleted');

  btnConvertAll.disabled = readyCount === 0;
  btnConvertAll.style.opacity = readyCount === 0 ? '0.5' : '1';

  btnDownloadZip.disabled = completedCount === 0;
  btnDownloadZip.style.opacity = completedCount === 0 ? '0.5' : '1';
  btnDownloadZip.querySelector('.zip-count').textContent = completedCount > 0 ? `(${completedCount})` : '';

  btnClearCompleted.style.display = completedCount > 0 ? 'inline-flex' : 'none';
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  const isError = type === 'error';
  const isSuccess = type === 'success';

  toast.className = `p-4 rounded-xl glass-panel shadow-2xl flex items-center gap-3 transition-all transform translate-y-2 duration-300 text-sm ${
    isError ? 'border-rose-500/50 text-rose-200' : isSuccess ? 'border-emerald-500/50 text-emerald-200' : 'text-slate-200'
  }`;

  toast.innerHTML = `
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => toast.classList.remove('translate-y-2'), 10);
  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
