/**
 * app.js — Dashboard narrativo con IA, gráficas y línea de tiempo histórica
 */

var estado = {
    datos: null,
    documentoActual: null,
    charts: {}
};

document.addEventListener('DOMContentLoaded', function () {
    configurarNavegacion();
    cargarDashboard();
    cargarStatusIA();
});

/* =========================================================================
   NAVEGACIÓN
   ========================================================================= */
function configurarNavegacion() {
    document.querySelectorAll('.nav-btn[data-view]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            cambiarVista(btn.getAttribute('data-view'));
        });
    });
    document.getElementById('searchBtn').addEventListener('click', ejecutarBusqueda);
    document.getElementById('searchInput').addEventListener('keyup', function (e) {
        if (e.key === 'Enter') ejecutarBusqueda();
    });
}

function cambiarVista(vistaId) {
    document.querySelectorAll('.nav-btn[data-view]').forEach(function (b) {
        b.classList.toggle('active', b.getAttribute('data-view') === vistaId);
    });
    var viewName = 'view' + vistaId.charAt(0).toUpperCase() + vistaId.slice(1);
    document.querySelectorAll('.view').forEach(function (v) {
        v.classList.toggle('active', v.id === viewName);
    });
    if (vistaId === 'dashboard' && estado.datos) {
        renderizarDashboard(estado.datos.modulos);
    } else if (vistaId === 'timeline') {
        cargarTimeline();
    } else if (vistaId === 'explorar') {
        renderizarExplorar();
    }
}

/* =========================================================================
   STATUS IA
   ========================================================================= */
function cargarStatusIA() {
    fetch('/api/status').then(function (r) { return r.json(); }).then(function (data) {
        if (data.modulos_ia || data.timeline_ia || data.estadisticas_ia) {
            document.getElementById('iaBadge').style.display = 'block';
        }
    }).catch(function () {});
}

/* =========================================================================
   DASHBOARD
   ========================================================================= */
function cargarDashboard() {
    fetch('/api/modulos').then(function (r) { return r.json(); }).then(function (data) {
        estado.datos = data;
        document.getElementById('headerStats').innerHTML =
            '<span>' + data.total_modulos + ' módulos · ' + data.total_documentos + ' documentos</span>';
        var desc = document.getElementById('dashboardDesc');
        if (data.ia_enhanced) {
            desc.innerHTML = 'Este proyecto reúne <strong>' + data.total_documentos +
                '</strong> documentos académicos en <strong>' + data.total_modulos +
                '</strong> módulos. Las descripciones y conceptos han sido enriquecidos con IA.';
        } else {
            desc.innerHTML = 'Este proyecto reúne <strong>' + data.total_documentos +
                '</strong> documentos académicos organizados en <strong>' + data.total_modulos +
                '</strong> módulos. Explora la narrativa de la desaparición forzada en América Latina.';
        }
        renderizarDashboard(data.modulos);
        cargarEstadisticas();
    }).catch(function (err) {
        document.getElementById('moduloGrid').innerHTML = '<p class="loading">Error: ' + err.message + '</p>';
    });
}

function renderizarDashboard(modulos) {
    var grid = document.getElementById('moduloGrid');
    grid.innerHTML = '';
    var principales = modulos.filter(function (m) { return !m.es_complementario; });
    var complementarios = modulos.filter(function (m) { return m.es_complementario; });
    principales.forEach(function (mod, idx) {
        var card = document.createElement('div');
        card.className = 'modulo-card';

        var conceptosHtml = mod.conceptos_clave && mod.conceptos_clave.length
            ? '<div class="mod-conceptos">' + mod.conceptos_clave.slice(0, 6).map(function (c) {
                return '<span>' + (typeof c === 'string' ? c.split(':')[0] : c) + '</span>';
            }).join('') + '</div>' : '';

        var datosNumHtml = mod.datos_numericos && mod.datos_numericos.length
            ? '<div class="mod-datos-num">' + mod.datos_numericos.slice(0, 4).map(function (d) {
                return '<div class="mod-dato-item"><span class="dato-valor">' + d.valor + '</span><span class="dato-label">' + d.categoria + '</span></div>';
            }).join('') + '</div>' : '';

        var docsHtml = mod.documentos && mod.documentos.length
            ? '<div class="mod-docs-lista">' +
              mod.documentos.slice(0, 3).map(function (d) {
                  return '<div class="mod-doc-item-mini" title="' + d.titulo + '">📄 ' +
                      d.titulo.substring(0, 50) + (d.titulo.length > 50 ? '...' : '') + '</div>';
              }).join('') +
              (mod.documentos.length > 3 ? '<div class="mod-doc-mas">+' + (mod.documentos.length - 3) + ' más</div>' : '') +
              '</div>' : '';

        var reflexionHtml = mod.reflexion ? '<div class="mod-reflexion">' + mod.reflexion + '</div>' : '';

        card.innerHTML =
            '<div class="mod-numero">' + (idx + 1) + '</div>' +
            '<h3>' + mod.titulo + '</h3>' +
            (mod.subtitulo ? '<div class="mod-subtitulo">' + mod.subtitulo + '</div>' : '') +
            '<div class="mod-desc">' + mod.descripcion + '</div>' +
            conceptosHtml + datosNumHtml + docsHtml + reflexionHtml +
            '<div class="mod-meta"><span>' + mod.total_docs + ' documentos</span></div>' +
            (mod.epoca ? '<div class="mod-epoca">' + mod.epoca + '</div>' : '');

        card.addEventListener('click', function () {
            cambiarVista('explorar');
            setTimeout(function () { abrirModulo(mod.id); }, 100);
        });
        grid.appendChild(card);
    });
    if (complementarios.length) {
        var compSection = document.createElement('div');
        compSection.className = 'modulo-complementario-section';
        var compHtml = '<h4>📎 Material complementario transversal</h4>';
        compHtml += '<p>Los siguientes documentos proveen las bases conceptuales y contextuales que sustentan todos los módulos del diplomado.</p>';
        complementarios.forEach(function (comp) {
            compHtml += '<div class="modulo-complementario" onclick="cambiarVista(\'explorar\')">';
            compHtml += '<h5>' + comp.titulo + '</h5>';
            compHtml += '<p>' + comp.descripcion + '</p>';
            compHtml += '<span class="mod-meta">' + comp.total_docs + ' documentos</span>';
            compHtml += '</div>';
        });
        compSection.innerHTML = compHtml;
        grid.appendChild(compSection);
    }
}

/* =========================================================================
   GRÁFICAS — Datos históricos reales de desaparición forzada
   ========================================================================= */
function cargarEstadisticas() {
    fetch('/api/estadisticas').then(function (r) { return r.json(); }).then(function (data) {
        document.getElementById('chartsSection').style.display = 'block';
        renderizarGraficas(data);
    }).catch(function () {});
}

function renderizarGraficas(data) {
    var hist = data.datos_historicos || {};

    // 1. Desaparecidos por país — gráfico de barras horizontal
    var paises = (hist.cifras_mundo || hist.desaparecidos_por_pais || []).slice().sort(function (a, b) { return b.cifra - a.cifra; });
    if (paises.length) {
        var ctx = document.getElementById('chartPaises');
        if (ctx) {
            destruirChart('chartPaises');
            var colores = ['#c94c4c', '#d66a4a', '#e08848', '#c9a84c', '#a88830', '#8b5e3c', '#6b4528', '#5a3520'];
            estado.charts.chartPaises = new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: paises.map(function (p) { return p.pais; }),
                    datasets: [{
                        label: 'Personas desaparecidas (estimado)',
                        data: paises.map(function (p) { return p.cifra; }),
                        backgroundColor: colores.slice(0, paises.length),
                        borderRadius: 3
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#2a2a2a', titleColor: '#c9a84c', bodyColor: '#e0e0e0',
                            callbacks: {
                                afterLabel: function (ctx) {
                                    var p = paises[ctx.dataIndex];
                                    return 'Período: ' + (p.periodo || '') + '\nFuente: ' + (p.fuente || '');
                                }
                            }
                        }
                    },
                    scales: {
                        x: { ticks: { color: '#707070', callback: function (v) { return v >= 1000 ? (v/1000).toFixed(0) + 'k' : v; } }, grid: { color: '#2a2a2a' } },
                        y: { ticks: { color: '#a0a0a0' }, grid: { display: false } }
                    }
                }
            });
        }
    }

    // 2. Tendencia por década — línea de tiempo
    var tendencia = hist.tendencia_por_decada || [];
    if (tendencia.length) {
        var ctx2 = document.getElementById('chartTemporal');
        if (ctx2) {
            destruirChart('chartTemporal');
            estado.charts.chartTemporal = new Chart(ctx2.getContext('2d'), {
                type: 'line',
                data: {
                    labels: tendencia.map(function (d) { return d.decada; }),
                    datasets: [{
                        label: 'Desaparecidos (estimado)',
                        data: tendencia.map(function (d) { return d.desaparecidos_estimados; }),
                        borderColor: '#c9a84c',
                        backgroundColor: 'rgba(201, 168, 76, 0.1)',
                        fill: true,
                        tension: 0.3,
                        pointBackgroundColor: '#c9a84c',
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        tooltip: {
                            backgroundColor: '#2a2a2a', titleColor: '#c9a84c', bodyColor: '#e0e0e0',
                            callbacks: {
                                afterLabel: function (ctx) {
                                    return tendencia[ctx.dataIndex].descripcion;
                                }
                            }
                        }
                    },
                    scales: {
                        y: { ticks: { color: '#707070', callback: function (v) { return v >= 1000 ? (v/1000).toFixed(0) + 'k' : v; } }, grid: { color: '#2a2a2a' } },
                        x: { ticks: { color: '#a0a0a0' }, grid: { display: false } }
                    }
                }
            });
        }
    }

    // 3. Datos clave impactantes — tarjetas
    var datosClave = hist.datos_clave || [];
    if (datosClave.length) {
        var ctx3 = document.getElementById('chartDocsPorModulo');
        if (ctx3) {
            // Usar este canvas para mostrar tarjetas de datos clave
            // Ocultar el canvas y mostrar texto
            ctx3.style.display = 'none';
            var parent = ctx3.parentElement;
            var html = '<div style="padding:10px">';
            datosClave.forEach(function (d) {
                html += '<div class="dato-impactante">' +
                    '<div class="di-valor">' + d.valor + '</div>' +
                    '<div class="di-categoria">' + d.categoria + '</div>' +
                    '<div class="di-contexto">' + d.contexto + '</div>' +
                    '</div>';
            });
            html += '</div>';
            // Solo agregar si no existe ya
            if (!parent.querySelector('.dato-impactante')) {
                parent.insertAdjacentHTML('beforeend', html);
            }
        }
    }

    // 4. Docs por módulo — gráfico de barras simple
    var mods = (data.docs_por_modulo || []).slice().sort(function (a, b) { return b.cantidad - a.cantidad; });
    if (mods.length) {
        var ctx4 = document.getElementById('chartTematico');
        if (ctx4) {
            destruirChart('chartTematico');
            var coloresMod = ['#c9a84c', '#a88830', '#8b5e3c', '#6b4528', '#5a3520', '#c9a84c', '#a88830', '#8b5e3c', '#6b4528', '#5a3520'];
            estado.charts.chartTematico = new Chart(ctx4.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: mods.map(function (m) { return m.modulo.length > 15 ? m.modulo.substring(0, 15) + '…' : m.modulo; }),
                    datasets: [{
                        label: 'Documentos',
                        data: mods.map(function (m) { return m.cantidad; }),
                        backgroundColor: coloresMod.slice(0, mods.length),
                        borderRadius: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { color: '#707070', stepSize: 1 }, grid: { color: '#2a2a2a' } },
                        x: { ticks: { color: '#a0a0a0', maxRotation: 45, font: { size: 9 } }, grid: { display: false } }
                    }
                }
            });
        }
    }
}

function destruirChart(id) {
    if (estado.charts[id]) { estado.charts[id].destroy(); delete estado.charts[id]; }
}

/* =========================================================================
   LÍNEA DE TIEMPO — Agrupada por período histórico
   ========================================================================= */
function cargarTimeline() {
    var container = document.getElementById('timelineContainer');
    container.innerHTML = '<p class="loading">Cargando línea de tiempo histórica...</p>';

    fetch('/api/timeline').then(function (r) { return r.json(); }).then(function (eventos) {
        container.innerHTML = '';

        // Agrupar por período
        var periodos = {};
        eventos.forEach(function (ev) {
            var per = ev.periodo || 'Otros';
            if (!periodos[per]) periodos[per] = [];
            periodos[per].push(ev);
        });

        var ordenPeriodos = Object.keys(periodos);
        ordenPeriodos.forEach(function (periodo, pi) {
            var evts = periodos[periodo];
            var minYear = evts.length ? Math.min.apply(null, evts.map(function (e) { return e.año || 9999; })) : '';
            var maxYear = evts.length ? Math.max.apply(null, evts.map(function (e) { return e.año || 0; })) : '';

            // Encabezado de período
            var perHeader = document.createElement('div');
            perHeader.className = 'tl-periodo-header';
            perHeader.innerHTML = '<div class="tl-periodo-bar"></div><h3>' + periodo + '</h3>';
            container.appendChild(perHeader);

            // Eventos del período
            evts.forEach(function (ev) {
                var item = document.createElement('div');
                item.className = 'timeline-item';
                item.setAttribute('data-num', ev.id);

                var paisHtml = ev.paises && ev.paises.length
                    ? '<div class="tl-paises">' + ev.paises.map(function (p) {
                        return '<span>' + p + '</span>';
                    }).join('') + '</div>' : '';

                var tipoLabel = (ev.tipo || '').replace(/_/g, ' ');

                item.innerHTML =
                    '<div class="timeline-card">' +
                    '<div class="tl-header">' +
                    (ev.año ? '<span class="tl-year">' + ev.año + '</span>' : '') +
                    (tipoLabel ? '<span class="tl-tipo">' + tipoLabel + '</span>' : '') +
                    '</div>' +
                    '<h4>' + ev.evento + '</h4>' +
                    '<p>' + ev.descripcion + '</p>' +
                    paisHtml +
                    '</div>';

                container.appendChild(item);
            });
        });
    }).catch(function () {
        container.innerHTML = '<p class="loading">Error al cargar la línea de tiempo.</p>';
    });
}

/* =========================================================================
   EXPLORAR MÓDULOS + CONEXIONES
   ========================================================================= */
function renderizarExplorar() {
    var modulos = estado.datos ? estado.datos.modulos : [];
    var container = document.getElementById('moduloList');
    container.innerHTML = '';

    // Título con conexiones
    var header = document.createElement('div');
    header.className = 'explorar-intro';
    header.innerHTML = '<h2>Recorrido por los módulos</h2><p>Cada módulo se conecta con el siguiente para construir una narrativa integral sobre la desaparición forzada en América Latina.</p>';
    container.appendChild(header);

    // Cargar conexiones
    fetch('/api/conexiones').then(function (r) { return r.json(); }).then(function (conexiones) {
        var connMap = {};
        conexiones.forEach(function (c) { connMap[c.de] = c; });

        // Módulos en orden (1-9 + adicionales aparte)
        var ordenModulos = ['modulo1', 'modulo2', 'modulo3', 'modulo4', 'modulo5', 'modulo 6', 'modulo7', 'modulo8', 'modulo9'];
        var modMap = {};
        modulos.forEach(function (m) { modMap[m.id] = m; });

        ordenModulos.forEach(function (id, idx) {
            var mod = modMap[id];
            if (!mod) return;

            var group = document.createElement('div');
            group.className = 'modulo-group';
            group.id = 'mod-' + id.replace(/\s+/g, '_');

            var header = document.createElement('div');
            header.className = 'modulo-group-header';
            header.innerHTML =
                '<div class="mod-g-numero">' + (idx + 1) + '</div>' +
                '<div class="mod-g-titulos">' +
                '<h3>' + mod.titulo + '</h3>' +
                (mod.epoca ? '<span class="mod-g-meta">' + mod.epoca + '</span>' : '') +
                '</div>' +
                '<div><span class="mod-g-meta">' + mod.total_docs + ' docs</span><span class="mod-g-toggle">▼</span></div>';

            var body = document.createElement('div');
            body.className = 'modulo-group-body';
            body.innerHTML = '<div class="mod-desc">' + mod.descripcion + '</div>';

            if (mod.conceptos_clave && mod.conceptos_clave.length) {
                body.innerHTML += '<div class="mod-conceptos">' +
                    mod.conceptos_clave.map(function (c) {
                        return '<span>' + (typeof c === 'string' ? c.split(':')[0] : c) + '</span>';
                    }).join('') + '</div>';
            }

            // Documentos
            mod.documentos.forEach(function (doc) {
                var item = document.createElement('div');
                item.className = 'mod-doc-item';
                item.innerHTML =
                    '<span class="doc-titulo">📄 ' + doc.titulo + '</span>' +
                    '<span class="doc-tamano">' + doc.tamano_kb + ' KB</span>' +
                    '<button class="doc-btn" onclick="abrirDocumento(\'' +
                    encodeURIComponent(doc.ruta_relativa) + '\', \'' +
                    escaparComillas(doc.titulo) + '\')">Abrir</button>';
                body.appendChild(item);
            });

            group.appendChild(header);
            group.appendChild(body);
            header.addEventListener('click', function () { group.classList.toggle('open'); });
            container.appendChild(group);

            // Conexión narrativa (excepto después del último)
            var conn = connMap[id];
            if (conn) {
                var connEl = document.createElement('div');
                connEl.className = 'mod-conexion';
                connEl.innerHTML =
                    '<div class="conn-arrow">↓</div>' +
                    '<div class="conn-narrativa">' +
                    '<div class="conn-label">Conexión con ' + conn.a_titulo + ':</div>' +
                    '<p>' + conn.narrativa + '</p>' +
                    '</div>';
                container.appendChild(connEl);
            }
        });

        // Material complementario al final
        var adic = modMap['adicionales'];
        if (adic) {
            var compSection = document.createElement('div');
            compSection.className = 'modulo-complementario-section';
            compSection.id = 'mod-adicionales';
            var introHtml =
                '<div class="complementario-intro">' +
                '<h3>Material complementario transversal</h3>' +
                '<p>Los siguientes documentos proveen las bases conceptuales y contextuales que sustentan todos los módulos del diplomado. Se recomienda su lectura como apoyo transversal al recorrido formativo.</p>' +
                '</div>';
            var docsHtml = '<div class="complementario-docs">';
            adic.documentos.forEach(function (doc) {
                docsHtml +=
                    '<div class="complementario-doc-item">' +
                    '<span class="doc-titulo">📄 ' + doc.titulo + '</span>' +
                    '<span class="doc-tamano">' + doc.tamano_kb + ' KB</span>' +
                    '<button class="doc-btn" onclick="abrirDocumento(\'' +
                    encodeURIComponent(doc.ruta_relativa) + '\', \'' +
                    escaparComillas(doc.titulo) + '\')">Abrir</button>' +
                    '</div>';
            });
            docsHtml += '</div>';
            compSection.innerHTML = introHtml + docsHtml;
            container.appendChild(compSection);
        }
    }).catch(function () {
        // Fallback: mostrar módulos sin conexiones
        renderizarListaModulosSimple(modulos, container);
    });
}

function renderizarListaModulosSimple(modulos, container) {
    modulos.forEach(function (mod) {
        var group = document.createElement('div');
        group.className = 'modulo-group';
        group.id = 'mod-' + mod.id.replace(/\s+/g, '_');
        var header = document.createElement('div');
        header.className = 'modulo-group-header';
        header.innerHTML = '<div><h3>' + mod.titulo + '</h3>' + (mod.epoca ? '<span class="mod-g-meta">' + mod.epoca + '</span>' : '') + '</div>' +
            '<div><span class="mod-g-meta">' + mod.total_docs + ' docs</span><span class="mod-g-toggle">▼</span></div>';
        var body = document.createElement('div');
        body.className = 'modulo-group-body';
        mod.documentos.forEach(function (doc) {
            var item = document.createElement('div');
            item.className = 'mod-doc-item';
            item.innerHTML = '<span class="doc-titulo">📄 ' + doc.titulo + '</span><span class="doc-tamano">' + doc.tamano_kb + ' KB</span>' +
                '<button class="doc-btn" onclick="abrirDocumento(\'' + encodeURIComponent(doc.ruta_relativa) + '\', \'' + escaparComillas(doc.titulo) + '\')">Abrir</button>';
            body.appendChild(item);
        });
        group.appendChild(header);
        group.appendChild(body);
        header.addEventListener('click', function () { group.classList.toggle('open'); });
        container.appendChild(group);
    });
}

function abrirModulo(modId) {
    var el = document.getElementById('mod-' + modId.replace(/\s+/g, '_'));
    if (el) { el.classList.add('open'); el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
}

/* =========================================================================
   MODAL
   ========================================================================= */
function abrirDocumento(rutaRelativa, titulo) {
    estado.documentoActual = { ruta: rutaRelativa, titulo: titulo };
    document.getElementById('modalDocTitle').textContent = titulo;
    document.querySelectorAll('.tab-pane').forEach(function (p) { p.classList.remove('active'); });
    document.querySelectorAll('.tab-btn').forEach(function (b) { b.classList.remove('active'); });
    document.getElementById('tabTexto').classList.add('active');
    document.querySelector('.tab-btn[data-tab="texto"]').classList.add('active');

    document.getElementById('docTextContent').innerHTML = '<p class="loading">Cargando texto...</p>';
    fetch('/api/documento/' + rutaRelativa).then(function (r) { return r.json(); }).then(function (data) {
        document.getElementById('docTextContent').innerHTML = '<p>' + data.texto.replace(/\n/g, '</p><p>') + '</p>';
    }).catch(function () {
        document.getElementById('docTextContent').innerHTML = '<p class="loading">Error al cargar.</p>';
    });

    document.getElementById('pdfViewer').innerHTML = '<iframe src="/api/pdf/' + rutaRelativa + '" title="PDF"></iframe>';
    document.getElementById('docModal').classList.add('open');
}

function cerrarModal() {
    document.getElementById('docModal').classList.remove('open');
    estado.documentoActual = null;
    document.getElementById('pdfViewer').innerHTML = '';
}

function cambiarTab(tab) {
    document.querySelectorAll('.tab-pane').forEach(function (p) { p.classList.remove('active'); });
    document.querySelectorAll('.tab-btn').forEach(function (b) { b.classList.remove('active'); });
    document.getElementById('tab' + tab.charAt(0).toUpperCase() + tab.slice(1)).classList.add('active');
    document.querySelector('.tab-btn[data-tab="' + tab + '"]').classList.add('active');
}

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && document.getElementById('docModal').classList.contains('open')) { cerrarModal(); }
});

/* =========================================================================
   BÚSQUEDA
   ========================================================================= */
function ejecutarBusqueda() {
    var q = document.getElementById('searchInput').value.trim();
    if (!q) return;
    cambiarVista('explorar');

    fetch('/api/buscar?q=' + encodeURIComponent(q)).then(function (r) { return r.json(); }).then(function (data) {
        var c = document.getElementById('moduloList');
        if (!data.resultados.length) {
            c.innerHTML = '<div class="search-results"><h3>Búsqueda: "' + q + '"</h3><p>Sin resultados.</p></div>';
            return;
        }
        var html = '<div class="search-results"><h3>Búsqueda: "' + q + '" — ' + data.total + ' resultado(s)</h3>';
        data.resultados.forEach(function (doc) {
            html += '<div class="search-result-item"><span class="sr-titulo">📄 ' + doc.titulo + '</span>' +
                '<span class="sr-modulo">' + doc.modulo_titulo + '</span>' +
                '<button class="sr-btn" onclick="abrirDocumento(\'' + encodeURIComponent(doc.ruta_relativa) +
                '\', \'' + escaparComillas(doc.titulo) + '\')">Abrir</button></div>';
        });
        c.innerHTML = html;
    }).catch(function () {
        document.getElementById('moduloList').innerHTML = '<p class="loading">Error en búsqueda.</p>';
    });
}

/* =========================================================================
   UTILIDADES
   ========================================================================= */
function escaparComillas(str) { return str.replace(/'/g, "\\'").replace(/"/g, '&quot;'); }
