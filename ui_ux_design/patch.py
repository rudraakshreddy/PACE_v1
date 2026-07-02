import sys

with open('script.js', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '    const tabButtons = {'
end_seq = 'This module is under development and will be integrated in the next projection phase.\';\n                }\n            });\n        }\n    });'
start_idx = content.find(start_marker)
end_idx = content.find(end_seq)

if start_idx == -1 or end_idx == -1:
    print('Markers not found')
    sys.exit(1)

end_idx += len(end_seq)

replacement_tabs = '''    const tabButtons = {
        'file-tab-btn': { viewId: 'file-panel-view' },
        'project-details-tab-btn': { viewId: 'project-details-panel-view' },
        'feed-data-tab-btn': { viewId: 'feed-dashboard-view' },
        'calculation-tab-btn': { viewId: 'calculation-panel-view' },
        'scaling-tab-btn': { viewId: 'scaling-panel-view' },
        'process-tab-btn': { viewId: 'process-dashboard-view' },
        'aging-tab-btn': { viewId: 'aging-panel-view' },
        'report-tab-btn': { viewId: 'report-panel-view' }
    };

    const views = Object.values(tabButtons).map(info => document.getElementById(info.viewId)).filter(Boolean);
    const placeholderView = document.getElementById('tab-placeholder-view');

    Object.keys(tabButtons).forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', (e) => {
                if (btn.classList.contains('pace-locked-tab')) {
                    const toast = document.getElementById('pace-lock-toast');
                    if (toast) {
                        toast.style.display = 'flex';
                        setTimeout(() => { toast.style.display = 'none'; }, 3000);
                    }
                    return; // PREVENT TAB SWITCH
                }

                // Set active class
                document.querySelectorAll('.menu-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                localStorage.setItem('activeTabId', id);

                // Hide all views
                views.forEach(v => { if(v) v.style.display = 'none'; });
                if (placeholderView) placeholderView.style.display = 'none';

                // Show selected view
                const viewId = tabButtons[id].viewId;
                const view = document.getElementById(viewId);
                if (view) {
                    if (viewId === 'project-details-panel-view' || viewId === 'file-panel-view') {
                        view.style.display = 'flex';
                    } else {
                        view.style.display = 'grid';
                    }
                } else if (placeholderView) {
                    placeholderView.style.display = 'flex';
                }

                // specific tab logic
                if (id === 'aging-tab-btn') {
                    if(typeof syncAllParametersFromFeed === 'function') syncAllParametersFromFeed();
                } else if (id === 'calculation-tab-btn') {
                    if (typeof window.updateLivePFD === 'function') window.updateLivePFD();
                    
                    fetch('http://localhost:8000/api/membranes')
                        .then(res => res.json())
                        .then(data => {
                            if(data.ro_membranes) {
                                const roSel = document.getElementById('calc-ro-membrane');
                                if(roSel) roSel.innerHTML = data.ro_membranes.map(m => `<option value="${m.id}">${m.name} (${m.type})</option>`).join('');
                            }
                            if(data.uf_modules) {
                                const ufSel = document.getElementById('calc-uf-module');
                                if(ufSel) ufSel.innerHTML = data.uf_modules.map(m => `<option value="${m.id}">${m.name}</option>`).join('');
                            }
                        })
                        .catch(err => console.error('Failed to load membrane DB', err));
                } else if (id === 'report-tab-btn') {
                    if (typeof generateReportContent === 'function') generateReportContent();
                }
            });
        }
    });
'''

top_matter = '''window.isProjectDirty = false;

window.showLoader = function() {
    const loader = document.getElementById('global-loader');
    if (loader) loader.classList.add('is-active');
};

window.hideLoader = function() {
    const loader = document.getElementById('global-loader');
    if (loader) loader.classList.remove('is-active');
};

const originalFetch = window.fetch;
window.fetch = async function(...args) {
    window.showLoader();
    try {
        return await originalFetch(...args);
    } finally {
        window.hideLoader();
    }
};

window.validateProjectModal = function() {
    const pName = document.getElementById('proj-name');
    const pEng = document.getElementById('proj-engineer');
    if (pName && pEng && pName.value.trim() !== '' && pEng.value.trim() !== '') {
        document.querySelectorAll('.pace-locked-tab').forEach(btn => {
            btn.classList.remove('pace-locked-tab');
            const icon = btn.querySelector('.pace-lock-icon');
            if (icon) icon.style.display = 'none';
        });
        window.isProjectDirty = true;
    } else {
        document.querySelectorAll('.menu-btn:not(#project-details-tab-btn):not(#file-tab-btn)').forEach(btn => {
            btn.classList.add('pace-locked-tab');
            const icon = btn.querySelector('.pace-lock-icon');
            if (icon) icon.style.display = 'inline-block';
        });
    }
};

window.clearProjectModal = function() {
    const pName = document.getElementById('proj-name');
    const pEng = document.getElementById('proj-engineer');
    if (pName) pName.value = '';
    if (pEng) pEng.value = '';
    window.validateProjectModal();
};

window.addEventListener('beforeunload', (e) => {
    if (window.isProjectDirty) {
        e.preventDefault();
        e.returnValue = '';
    }
});

document.addEventListener('input', () => { window.isProjectDirty = true; });

// Make sure to unlock on load if there's data
window.addEventListener('load', () => {
    setTimeout(window.validateProjectModal, 500);
});
'''

bottom_matter = '''
window.syncFeedToAging = function() {
    const sdiFeed = document.getElementById('sdi');
    const sdiAging = document.getElementById('aging-sdi');
    if (sdiFeed && sdiAging) sdiAging.value = sdiFeed.value;

    const tocFeed = document.getElementById('toc');
    const tocAging = document.getElementById('aging-toc');
    if (tocFeed && tocAging) tocAging.value = tocFeed.value;

    const tempFeed = document.getElementById('temp');
    const tempAging = document.getElementById('aging-temp');
    if (tempFeed && tempAging) tempAging.value = tempFeed.value;
};

document.addEventListener('DOMContentLoaded', () => {
    const sdiFeed = document.getElementById('sdi');
    const tocFeed = document.getElementById('toc');
    const tempFeed = document.getElementById('temp');
    if (sdiFeed) sdiFeed.addEventListener('input', window.syncFeedToAging);
    if (tocFeed) tocFeed.addEventListener('input', window.syncFeedToAging);
    if (tempFeed) tempFeed.addEventListener('input', window.syncFeedToAging);
});
'''

new_content = top_matter + content[:start_idx] + replacement_tabs + content[end_idx:] + bottom_matter

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Patched script.js successfully')
