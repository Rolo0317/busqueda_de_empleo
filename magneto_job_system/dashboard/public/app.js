const state = {
  search: '',
  logs: []
};

const currencySafe = (value) => value || 'No especificado';

const loadDashboard = async () => {
  const response = await fetch(`/api/dashboard?search=${encodeURIComponent(state.search)}`);
  const data = await response.json();
  renderStats(data.stats);
  renderJobs(data.jobs);
  renderSearches(data.searches);
};

const renderStats = (stats) => {
  document.querySelector('#stat-total').textContent = stats.total_jobs || 0;
  document.querySelector('#stat-applied').textContent = stats.applied_jobs || 0;
  document.querySelector('#stat-score').textContent = `${Math.round(stats.avg_score || 0)}%`;
  document.querySelector('#stat-priority').textContent = stats.high_priority_count || 0;
};

const renderJobs = (jobs) => {
  document.querySelector('#jobs').innerHTML = jobs.map((job) => `
    <tr class="border-t border-slate-800 hover:bg-slate-800/50 transition">
      <td class="p-3">
        <a href="${job.url}" target="_blank" class="font-semibold text-emerald-300 hover:underline">${job.title}</a>
        <p class="text-slate-500">${job.location || ''}</p>
      </td>
      <td class="p-3">${job.company_name}</td>
      <td class="p-3">${currencySafe(job.salary)}</td>
      <td class="p-3">
        <span class="px-2 py-1 rounded-full ${job.match_score >= 70 ? 'bg-emerald-500/10 text-emerald-300' : 'bg-slate-700 text-slate-300'}">${job.match_score}%</span>
      </td>
      <td class="p-3">${job.status}</td>
    </tr>
  `).join('');
};

const renderSearches = (searches) => {
  document.querySelector('#searches').innerHTML = searches.map((item) => `
    <div class="bg-slate-950 rounded-lg p-3">
      <p class="font-semibold">${item.keyword}</p>
      <p class="text-slate-500 text-sm">${item.status} | ${item.jobs_found} vacantes</p>
    </div>
  `).join('');
};

const renderLogs = () => {
  document.querySelector('#logs').innerHTML = state.logs.slice(-120).map((log) => `
    <div class="${log.level === 'error' ? 'text-red-300' : log.level === 'warn' ? 'text-yellow-300' : 'text-slate-300'}">
      ${new Date(log.timestamp || log.created_at).toLocaleTimeString()} ${log.level?.toUpperCase?.() || 'INFO'} ${log.message}
    </div>
  `).join('');
};

document.querySelector('#refresh').addEventListener('click', loadDashboard);
document.querySelector('#search').addEventListener('input', (event) => {
  state.search = event.target.value;
  loadDashboard();
});

const events = new EventSource('/events');
events.onmessage = (event) => {
  state.logs.push(JSON.parse(event.data));
  renderLogs();
  loadDashboard();
};

loadDashboard();
fetch('/api/logs')
  .then((response) => response.json())
  .then((logs) => {
    state.logs = logs.map((log) => ({
      timestamp: log.created_at,
      level: log.level,
      message: log.message
    }));
    renderLogs();
  });
