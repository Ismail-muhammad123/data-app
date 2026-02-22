function initJazzminFix() {
    console.log("Jazzmin UI enhancements initialized");

    // 1. Smooth transition for sections not responding
    document.addEventListener('click', function (e) {
        const tabLink = e.target.closest('.nav-tabs a, .nav-pills a, [data-toggle="tab"], [data-toggle="pill"]');
        if (tabLink) {
            let href = tabLink.getAttribute('href');
            if (href && href.includes('#')) {
                href = '#' + href.split('#')[1];
            }
            if (href && href.startsWith('#')) {
                e.preventDefault();

                let jq = (typeof $ !== 'undefined') ? $ : ((typeof jQuery !== 'undefined') ? jQuery : null);
                if (jq && jq.fn && jq.fn.tab) {
                    jq(tabLink).tab('show');
                    return;
                }

                try {
                    const targetPane = document.querySelector(href);
                    if (targetPane) {
                        const contentContainer = targetPane.closest('.tab-content');
                        if (contentContainer) {
                            Array.from(contentContainer.children).forEach(pane => {
                                if (pane.classList.contains('tab-pane')) {
                                    pane.classList.remove('active', 'show');
                                }
                            });
                        }

                        const navContainer = tabLink.closest('.nav');
                        if (navContainer) {
                            navContainer.querySelectorAll('.nav-link').forEach(link => {
                                link.classList.remove('active');
                            });
                        }

                        targetPane.classList.add('active', 'show');
                        tabLink.classList.add('active');
                    }
                } catch (err) {
                    console.error("Tab switch error:", err);
                }
            }
        }
    });

    // 2. Mobile-friendly horizontal tabs
    const tabNavs = document.querySelectorAll('.nav-tabs');
    tabNavs.forEach(nav => {
        if (!nav.classList.contains('flex-column')) {
            nav.style.flexWrap = 'nowrap';
            nav.style.overflowX = 'auto';
            nav.style.overflowY = 'hidden';
            nav.style.webkitOverflowScrolling = 'touch';
            nav.style.msOverflowStyle = '-ms-autohiding-scrollbar';

            nav.style.scrollbarWidth = 'none'; // Firefox
            if (!document.getElementById('jazzmin-tab-fix-style')) {
                const style = document.createElement('style');
                style.id = 'jazzmin-tab-fix-style';
                style.innerHTML = `
                    .nav-tabs::-webkit-scrollbar { display: none; }
                    .nav-tabs { border-bottom: 2px solid #dee2e6; margin-bottom: 1rem; }
                    .nav-tabs .nav-link { white-space: nowrap; border: none !important; border-bottom: 2px solid transparent !important; }
                    .nav-tabs .nav-link.active { border: none !important; border-bottom: 2px solid #2563eb !important; color: #2563eb !important; background: transparent !important; }
                `;
                document.head.appendChild(style);
            }
        }
    });

    // 3. Improve Group/Permission labels (simplified labels)
    function simplifyPermissionLabels() {
        const options = document.querySelectorAll('.selector-available select option, .selector-chosen select option');
        options.forEach(opt => {
            if (opt.dataset.labeled) return;
            const text = opt.textContent;
            if (text.includes('|')) {
                const parts = text.split('|');
                const model = parts[1] ? parts[1].trim() : '';
                const permission = parts[2] ? parts[2].trim() : '';
                if (model && permission) {
                    opt.textContent = `[${model.toUpperCase()}] ${permission}`;
                    opt.dataset.labeled = 'true';
                }
            }
        });
    }

    // Run periodically to catch dynamic updates in filter_horizontal
    setInterval(simplifyPermissionLabels, 1000);

    // 4. Enhanced UI for card headers in change forms
    document.querySelectorAll('.card-header').forEach(header => {
        if (header.textContent.includes('Permissions') || header.textContent.includes('Authentication')) {
            header.style.backgroundColor = 'rgba(37, 99, 235, 0.03)';
            header.style.borderLeft = '4px solid #2563eb';
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initJazzminFix);
} else {
    initJazzminFix();
}
