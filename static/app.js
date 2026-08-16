document.addEventListener('DOMContentLoaded', () => {
    // === ESTADO GLOBAL DE LA APLICACIÓN ===
    let currentUser = null;
    let cloudBudgets = [];
    let budgetItems = [];
    let currentBudgetId = null;
    let bcvRate = 36.50;
    let uploadedFile = null;
    let chatHistory = [];
    let currentPaymentTab = 'paypal';

    // === ELEMENTOS DEL DOM ===
    // Contenedores de Vistas principales
    const landingPage = document.getElementById('landingPage');
    const dashboardPage = document.getElementById('dashboardPage');
    const editorPage = document.getElementById('editorPage');

    // Elementos de Carga y Modales
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    const loginModal = document.getElementById('loginModal');
    const registerModal = document.getElementById('registerModal');
    const checkoutModal = document.getElementById('checkoutModal');
    const editModal = document.getElementById('editModal');
    const aiModal = document.getElementById('aiModal');
    const bomModal = document.getElementById('bomModal');

    // Campos de Perfil de Usuario
    const userDisplayName = document.getElementById('userDisplayName');
    const userPlanBadge = document.getElementById('userPlanBadge');
    const userAvatar = document.getElementById('userAvatar');
    const welcomeUserText = document.getElementById('welcomeUserText');
    const widgetPlanName = document.getElementById('widgetPlanName');
    const widgetPlanStatus = document.getElementById('widgetPlanStatus');
    const widgetLimitText = document.getElementById('widgetLimitText');
    const widgetUpgradeArea = document.getElementById('widgetUpgradeArea');
    const budgetsCountText = document.getElementById('budgetsCountText');

    // Grilla del Dashboard
    const budgetsGrid = document.getElementById('budgetsGrid');
    const budgetsEmptyState = document.getElementById('budgetsEmptyState');

    // Elementos del Editor
    const editorProjectTitle = document.getElementById('editorProjectTitle');
    const editorLimitIndicator = document.getElementById('editorLimitIndicator');
    const editorItemsCount = document.getElementById('editorItemsCount');
    const showCostsCheckbox = document.getElementById('showCosts');
    const bcvRateInput = document.getElementById('bcvRate');
    
    const clientNombre = document.getElementById('clientNombre');
    const clientTelefono = document.getElementById('clientTelefono');
    const clientUbicacion = document.getElementById('clientUbicacion');

    // Elementos de Imagen en el Editor
    const imageInput = document.getElementById('imageInput');
    const previewImage = document.getElementById('previewImage');
    const imagePlaceholder = document.getElementById('imagePlaceholder');
    const btnEliminarImagen = document.getElementById('btnEliminarImagen');
    const btnAnalizarIA = document.getElementById('btnAnalizarIA');

    // Elementos de Chatbot
    const chatInput = document.getElementById('chatInput');
    const btnSendChat = document.getElementById('btnSendChat');
    const chatMessages = document.getElementById('chatMessages');

    // Elementos de Autocomplete de Catálogo
    const catalogSearchInput = document.getElementById('catalogSearchInput');
    const catalogSearchResults = document.getElementById('catalogSearchResults');

    // Tabla del Presupuesto
    const tableBody = document.getElementById('tableBody');
    const totalUSDDisplay = document.getElementById('totalUSD');
    const totalVESDisplay = document.getElementById('totalVES');
    const totalPartidasDisplay = document.getElementById('totalPartidas');

    // Botones del Editor
    const btnGenerarPDF = document.getElementById('btnGenerarPDF');
    const btnGenerarApuPDF = document.getElementById('btnGenerarApuPDF');
    const btnGenerarMemoria = document.getElementById('btnGenerarMemoriaIA');
    const btnListaMateriales = document.getElementById('btnListaMateriales');
    const btnNuevoPresupuesto = document.getElementById('btnNuevoPresupuesto');

    // Capas de bloqueo (Pro Lock overlays)
    const chatLockedLayer = document.getElementById('chatLockedLayer');
    const aiAnalysisLockedLayer = document.getElementById('aiAnalysisLockedLayer');
    const apuPdfLockedLayer = document.getElementById('apuPdfLockedLayer');
    const memoriaLockedLayer = document.getElementById('memoriaLockedLayer');
    const bomLockedLayer = document.getElementById('bomLockedLayer');

    // Formateador de moneda
    const formatCurrency = (val) => parseFloat(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    // === 1. INICIALIZACIÓN Y SESIÓN ===
    async function verificarSesion() {
        try {
            const res = await fetch('/api/auth/me');
            const data = await res.json();
            if (data.logged_in) {
                currentUser = data.user;
                mostrarDashboard();
            } else {
                currentUser = null;
                mostrarLanding();
            }
        } catch (e) {
            console.error(e);
            mostrarLanding();
        }
    }

    function mostrarLanding() {
        landingPage.classList.remove('hidden');
        dashboardPage.classList.add('hidden');
        editorPage.classList.add('hidden');
    }

    async function mostrarDashboard() {
        landingPage.classList.add('hidden');
        dashboardPage.classList.remove('hidden');
        editorPage.classList.add('hidden');

        // Actualizar datos del perfil
        userDisplayName.textContent = currentUser.nombre;
        userAvatar.textContent = currentUser.nombre.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
        welcomeUserText.textContent = `¡Hola, ${currentUser.nombre.split(' ')[0]}!`;

        // Mostrar botón de Admin si el usuario tiene privilegios
        const adminBtn = document.getElementById('btnAdminPanel');
        if (adminBtn) {
            if (currentUser.is_admin) {
                adminBtn.classList.remove('hidden');
            } else {
                adminBtn.classList.add('hidden');
            }
        }

        // Badge de Plan
        userPlanBadge.className = currentUser.plan === 'pro' ? 'text-[10px] font-bold py-0.5 px-2.5 rounded-full uppercase bg-purple-500/20 text-purple-400 border border-purple-500/30' : 'text-[10px] font-bold py-0.5 px-2.5 rounded-full uppercase bg-slate-700 text-slate-300 border border-slate-600';
        userPlanBadge.textContent = currentUser.plan === 'pro' ? 'Plan Pro' : 'Plan Free';

        widgetPlanName.textContent = currentUser.plan === 'pro' ? 'Plan Pro' : 'Plan Free';
        widgetPlanStatus.className = currentUser.plan === 'pro' ? 'text-[9px] font-bold px-2 py-0.5 rounded-full uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-[9px] font-bold px-2 py-0.5 rounded-full uppercase bg-slate-700 text-slate-300 border border-slate-600';
        widgetPlanStatus.textContent = currentUser.plan === 'pro' ? 'Activo' : 'Básico';

        if (currentUser.plan === 'pro') {
            const expiryStr = currentUser.current_period_end ? new Date(currentUser.current_period_end).toLocaleDateString() : 'Indefinido';
            widgetLimitText.innerHTML = `Presupuestos ilimitados. Acceso a IA y APUs.<br/><span class="text-[10px] text-accentPurple font-bold mt-1 block"><i class="fa-solid fa-clock mr-1"></i>Vence: ${expiryStr}</span>`;
            widgetUpgradeArea.classList.add('hidden');
        } else {
            widgetLimitText.textContent = 'Límite: 1 Presupuesto (hasta 10 partidas).';
            widgetUpgradeArea.classList.remove('hidden');
        }

        // Cargar presupuestos del usuario
        await cargarPresupuestosNube();
    }

    verificarSesion();

    // === 2. AUTENTICACIÓN (LOGIN / REGISTRO / LOGOUT) ===
    window.openLoginModal = () => {
        loginModal.classList.remove('hidden');
        registerModal.classList.add('hidden');
    };
    window.closeLoginModal = () => loginModal.classList.add('hidden');
    window.openRegisterModal = () => {
        registerModal.classList.remove('hidden');
        loginModal.classList.add('hidden');
    };
    window.closeRegisterModal = () => registerModal.classList.add('hidden');

    window.switchAuthModal = (target) => {
        if (target === 'login') openLoginModal();
        else openRegisterModal();
    };

    window.handleRegister = async (e) => {
        e.preventDefault();
        const nombre = document.getElementById('registerNombre').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;

        showLoading('Registrando usuario...');
        try {
            const res = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, nombre })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Error en el registro');

            hideLoading();
            closeRegisterModal();
            // Iniciar sesión inmediatamente
            showLoading('Iniciando sesión...');
            const loginRes = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const loginData = await loginRes.json();
            if (!loginRes.ok) throw new Error(loginData.detail);

            currentUser = loginData.user;
            hideLoading();
            mostrarDashboard();
        } catch (error) {
            hideLoading();
            alert(error.message);
        }
    };

    window.handleLogin = async (e) => {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;

        showLoading('Validando credenciales...');
        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Error en el login');

            currentUser = data.user;
            hideLoading();
            closeLoginModal();
            mostrarDashboard();
        } catch (error) {
            hideLoading();
            alert(error.message);
        }
    };

    window.cerrarSesion = async () => {
        showLoading('Cerrando sesión...');
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
            currentUser = null;
            hideLoading();
            mostrarLanding();
        } catch (e) {
            hideLoading();
            mostrarLanding();
        }
    };

    // === 3. GESTIÓN DEL DASHBOARD Y PRESUPUESTOS EN LA NUBE ===
    async function cargarPresupuestosNube() {
        try {
            const res = await fetch('/api/presupuestos');
            const data = await res.json();
            if (data.status === 'success') {
                cloudBudgets = data.presupuestos;
                renderBudgetsGrid();
            }
        } catch (e) {
            console.error('Error cargando presupuestos:', e);
        }
    }

    function renderBudgetsGrid() {
        budgetsGrid.innerHTML = '';
        const limitCount = currentUser.plan === 'pro' ? 'Ilimitados' : '1';
        budgetsCountText.textContent = `Presupuestos creados: ${cloudBudgets.length} / ${limitCount}`;

        if (cloudBudgets.length === 0) {
            budgetsEmptyState.classList.remove('hidden');
            budgetsGrid.classList.add('hidden');
            return;
        }

        budgetsEmptyState.classList.add('hidden');
        budgetsGrid.classList.remove('hidden');

        cloudBudgets.forEach(b => {
            const dateStr = new Date(b.updated_at || b.created_at).toLocaleDateString('es-ES', {
                year: 'numeric', month: 'short', day: 'numeric'
            });
            const card = document.createElement('div');
            card.className = 'bg-bgPanel p-5 rounded-xl border border-borderClr hover:border-slate-500 transition-all flex flex-col justify-between gap-4';
            card.innerHTML = `
                <div class="flex flex-col gap-1.5">
                    <h4 class="font-bold text-white font-outfit text-base truncate" title="${b.nombre_proyecto}">${b.nombre_proyecto}</h4>
                    <p class="text-xs text-slate-400">Cliente: <span class="text-slate-300 font-semibold">${b.cliente}</span></p>
                    <p class="text-[10px] text-slate-500">Última actualización: ${dateStr}</p>
                </div>
                <div class="flex justify-between items-center border-t border-borderClr/60 pt-3 mt-1">
                    <div class="text-left">
                        <span class="text-xs text-slate-400 block font-semibold">Tasa: Bs. ${b.tasa_bcv.toFixed(2)}</span>
                    </div>
                    <div class="flex gap-2">
                        <button onclick="cargarPresupuestoParaEditar(${b.id})" class="bg-accentBlue/10 hover:bg-accentBlue hover:text-white text-accentBlue px-3 py-1.5 rounded text-xs transition-colors flex items-center gap-1 font-semibold border border-accentBlue/20">
                            <i class="fa-solid fa-pen"></i> Editar
                        </button>
                        <button onclick="eliminarPresupuestoNube(${b.id})" class="bg-red-500/10 hover:bg-accentRed hover:text-white text-accentRed px-2.5 py-1.5 rounded text-xs transition-colors border border-red-500/20" title="Eliminar Presupuesto">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            budgetsGrid.appendChild(card);
        });
    }

    window.crearNuevoPresupuesto = () => {
        // Validar límite para Free
        if (currentUser.plan !== 'pro' && cloudBudgets.length >= 1) {
            alert('El Plan Free está limitado a 1 solo presupuesto en la nube. Actualiza a Pro para tener presupuestos ilimitados.');
            return;
        }

        currentBudgetId = null;
        budgetItems = [];
        editorProjectTitle.value = 'Nuevo Proyecto de Obra';
        clientNombre.value = '';
        clientTelefono.value = '';
        clientUbicacion.value = '';
        bcvRateInput.value = bcvRate.toFixed(2);
        
        chatHistory = [];
        chatMessages.innerHTML = '<div class="text-slate-400 italic text-center mt-2" id="chatWelcomeMsg">Ingresa qué partidas deseas añadir, modificar o remover.</div>';

        mostrarEditor();
    };

    window.cargarPresupuestoParaEditar = async (id) => {
        showLoading('Cargando presupuesto de la nube...');
        try {
            const res = await fetch(`/api/presupuestos/${id}`);
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail);

            const p = data.presupuesto;
            currentBudgetId = p.id;
            editorProjectTitle.value = p.nombre_proyecto;
            clientNombre.value = p.cliente;
            clientTelefono.value = p.telefono || '';
            clientUbicacion.value = p.ubicacion || '';
            bcvRate = p.tasa_bcv || 36.50;
            bcvRateInput.value = bcvRate.toFixed(2);
            budgetItems = p.items || [];
            
            chatHistory = [];
            chatMessages.innerHTML = '<div class="text-slate-400 italic text-center mt-2" id="chatWelcomeMsg">Presupuesto cargado. Escríbeme qué quieres modificar.</div>';

            hideLoading();
            mostrarEditor();
        } catch (e) {
            hideLoading();
            alert(e.message);
        }
    };

    window.eliminarPresupuestoNube = async (id) => {
        if (!confirm('¿Estás seguro de que deseas eliminar este presupuesto de la nube de forma permanente?')) return;
        showLoading('Eliminando presupuesto...');
        try {
            const res = await fetch(`/api/presupuestos/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail);

            hideLoading();
            await cargarPresupuestosNube();
        } catch (e) {
            hideLoading();
            alert(e.message);
        }
    };

    function mostrarEditor() {
        landingPage.classList.add('hidden');
        dashboardPage.classList.add('hidden');
        editorPage.classList.remove('hidden');
        
        updateUIRestrictions();
        renderTable();
    }

    window.volverAlDashboard = async () => {
        showLoading('Cargando panel de control...');
        await verificarSesion();
        hideLoading();
    };

    window.guardarPresupuestoEnNube = async () => {
        if (!clientNombre.value.trim()) {
            alert('Por favor complete el nombre del Cliente antes de guardar.');
            return;
        }

        showLoading('Guardando en la nube...');
        try {
            const payload = {
                id: currentBudgetId,
                nombre_proyecto: editorProjectTitle.value.trim() || 'Proyecto de Obra',
                cliente: clientNombre.value.trim(),
                telefono: clientTelefono.value.trim(),
                ubicacion: clientUbicacion.value.trim(),
                tasa_bcv: parseFloat(bcvRateInput.value) || 36.50,
                items: budgetItems
            };

            const res = await fetch('/api/presupuestos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (!res.ok) throw new Error(data.detail || 'Fallo al guardar');

            currentBudgetId = data.id;
            hideLoading();
            alert('¡Presupuesto guardado con éxito en la nube!');
        } catch (e) {
            hideLoading();
            alert(e.message);
        }
    };

    // === 4. CONTROL DE LIMITACIONES DEL PLAN FREE / PRO ===
    function updateUIRestrictions() {
        const esPro = (currentUser.plan === 'pro');
        
        if (esPro) {
            // Desbloquear herramientas premium
            chatLockedLayer.classList.add('hidden');
            aiAnalysisLockedLayer.classList.add('hidden');
            apuPdfLockedLayer.classList.add('hidden');
            memoriaLockedLayer.classList.add('hidden');
            bomLockedLayer.classList.add('hidden');
            editorLimitIndicator.classList.add('hidden');
        } else {
            // Bloquear herramientas premium
            chatLockedLayer.classList.remove('hidden');
            chatLockedLayer.classList.add('flex');
            
            aiAnalysisLockedLayer.classList.remove('hidden');
            aiAnalysisLockedLayer.classList.add('flex');
            
            apuPdfLockedLayer.classList.remove('hidden');
            apuPdfLockedLayer.classList.add('flex');
            
            memoriaLockedLayer.classList.remove('hidden');
            memoriaLockedLayer.classList.add('flex');
            
            bomLockedLayer.classList.remove('hidden');
            bomLockedLayer.classList.add('flex');

            editorLimitIndicator.classList.remove('hidden');
            editorItemsCount.textContent = budgetItems.length;
        }
    }

    window.promptUpgrade = (featureName) => {
        if (confirm(`La herramienta '${featureName}' es exclusiva del Plan Pro.\n\n¿Deseas abrir la facturación para actualizar tu plan ahora?`)) {
            volverAlDashboard().then(() => {
                openCheckoutModal();
            });
        }
    };

    // === 5. SIMULACIÓN DE PAGOS EN EUR A TASA BCV (PAYPAL / TRANSFERENCIA) ===
    window.openCheckoutModal = () => {
        const EUR_PRICE = 29.99;
        const rate = parseFloat(bcvRateInput.value) || 36.50;
        const totalVES = EUR_PRICE * rate;

        document.getElementById('checkoutVESAmount').textContent = `Equivalente: Bs. ${formatCurrency(totalVES)}`;
        document.getElementById('checkoutTransferAmountVES').textContent = `Bs. ${formatCurrency(totalVES)}`;
        
        checkoutModal.classList.remove('hidden');
        switchPaymentTab('paypal');
    };

    window.closeCheckoutModal = () => checkoutModal.classList.add('hidden');

    window.switchPaymentTab = (tab) => {
        currentPaymentTab = tab;
        const tabBtnPaypal = document.getElementById('tabBtnPaypal');
        const tabBtnTransfer = document.getElementById('tabBtnTransfer');
        const panelPaypal = document.getElementById('panelPaypal');
        const panelTransfer = document.getElementById('panelTransfer');

        if (tab === 'paypal') {
            tabBtnPaypal.className = "flex-1 py-3 text-xs font-bold border-b-2 border-accentBlue text-white flex items-center justify-center gap-1.5 bg-bgPanel/30";
            tabBtnTransfer.className = "flex-1 py-3 text-xs font-bold border-b-2 border-transparent text-slate-400 hover:text-white flex items-center justify-center gap-1.5";
            panelPaypal.classList.remove('hidden');
            panelTransfer.classList.add('hidden');
        } else {
            tabBtnPaypal.className = "flex-1 py-3 text-xs font-bold border-b-2 border-transparent text-slate-400 hover:text-white flex items-center justify-center gap-1.5";
            tabBtnTransfer.className = "flex-1 py-3 text-xs font-bold border-b-2 border-accentPurple text-white flex items-center justify-center gap-1.5 bg-bgPanel/30";
            panelPaypal.classList.add('hidden');
            panelTransfer.classList.remove('hidden');
        }
    };

    window.handleMockPaypalPayment = async (e) => {
        e.preventDefault();
        const email = e.target.querySelector('input[type="email"]').value;
        
        closeCheckoutModal();
        showLoading('Conectando con pasarela segura de PayPal...');
        
        setTimeout(async () => {
            showLoading('Validando cuenta y procesando fondos (€29.99)...');
            setTimeout(async () => {
                try {
                    const res = await fetch('/api/saas/subscribe', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            metodo_pago: 'paypal',
                            referencia_pago: 'PAYPAL-' + Math.random().toString(36).substring(2, 9).toUpperCase()
                        })
                    });
                    const data = await res.json();
                    
                    hideLoading();
                    if (res.ok) {
                        alert('¡Pago completado con éxito a través de PayPal! Su plan Pro ya está activo.');
                        currentUser.plan = 'pro';
                        currentUser.status = 'active';
                        mostrarDashboard();
                    } else {
                        alert('Error procesando pago: ' + data.detail);
                    }
                } catch (err) {
                    hideLoading();
                    alert('Fallo de red: ' + err);
                }
            }, 2000);
        }, 1500);
    };

    window.handleMockTransferPayment = async (e) => {
        e.preventDefault();
        const banco = document.getElementById('transferBanco').value;
        const referencia = document.getElementById('transferReferencia').value;

        closeCheckoutModal();
        showLoading('Registrando reporte de transferencia...');
        
        setTimeout(async () => {
            showLoading('Validando transacción (€29.99 equivalente)...');
            setTimeout(async () => {
                try {
                    const res = await fetch('/api/saas/subscribe', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            metodo_pago: 'transferencia',
                            referencia_pago: `${banco.toUpperCase()}-${referencia}`
                        })
                    });
                    const data = await res.json();
                    
                    hideLoading();
                    if (res.ok) {
                        alert('¡Comprobante reportado con éxito! Se ha habilitado su plan Pro (aprobación automática de pruebas activa).');
                        currentUser.plan = 'pro';
                        currentUser.status = 'active';
                        mostrarDashboard();
                    } else {
                        alert('Error procesando reporte: ' + data.detail);
                    }
                } catch (err) {
                    hideLoading();
                    alert('Fallo de red: ' + err);
                }
            }, 1500);
        }, 1000);
    };

    // === 6. DIÁLOGOS Y CONEXIÓN CON IA DE ANÁLISIS E IMAGEN ===
    window.closeAiModal = () => aiModal.classList.add('hidden');
    
    btnAnalizarIA.addEventListener('click', () => {
        if (!uploadedFile) {
            alert('Por favor cargue una imagen render o fotografía primero.');
            return;
        }
        aiModal.classList.remove('hidden');
    });

    document.getElementById('btnIniciarAnalisis').addEventListener('click', async () => {
        const largo = document.getElementById('aiLargo').value || '4.00';
        const ancho = document.getElementById('aiAncho').value || '3.00';
        const alto = document.getElementById('aiAlto').value || '2.60';
        const req = document.getElementById('aiRequerimientos').value || '';

        closeAiModal();
        showLoading('Análisis 3D Multimodal con IA en progreso...');

        const formData = new FormData();
        formData.append('imagen', uploadedFile);
        formData.append('largo', largo);
        formData.append('ancho', ancho);
        formData.append('alto', alto);
        formData.append('requerimientos', req);

        try {
            const res = await fetch('/api/analizar', { method: 'POST', body: formData });
            const data = await res.json();
            
            hideLoading();
            if (res.ok && data.status === 'success') {
                const totalAdding = data.resultados.length;
                let added = 0;
                
                for (let partida of data.resultados) {
                    // Validar límite en tiempo real si el usuario es Free (máximo 10)
                    if (currentUser.plan !== 'pro' && budgetItems.length >= 10) {
                        alert('Se detuvo la inserción de partidas. Ha alcanzado el límite de 10 partidas de su Plan Free. Suscríbase para más.');
                        break;
                    }
                    addBudgetItem(partida);
                    added++;
                }
                
                renderTable();
                alert(`IA completada. Se agregaron ${added} de ${totalAdding} partidas encontradas al presupuesto.`);
            } else {
                alert('Fallo de la IA: ' + (data.detail || 'Error desconocido'));
            }
        } catch (e) {
            hideLoading();
            alert('Fallo de conexión al analizar: ' + e);
        }
    });

    // Carga de imágenes en el editor
    imageInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadedFile = e.target.files[0];
            const reader = new FileReader();
            reader.onload = (ev) => {
                previewImage.src = ev.target.result;
                previewImage.classList.remove('hidden');
                imagePlaceholder.classList.add('hidden');
            };
            reader.readAsDataURL(uploadedFile);
        }
    });

    btnEliminarImagen.addEventListener('click', () => {
        uploadedFile = null;
        imageInput.value = '';
        previewImage.src = '';
        previewImage.classList.add('hidden');
        imagePlaceholder.classList.remove('hidden');
    });

    // === 7. CHATBOT ASISTENTE CON GEMINI ===
    function appendChatMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = sender === 'user' ? 'bg-[#2a303c] text-accentBlue p-2 rounded self-end max-w-[80%]' : 'bg-[#1e1e1e] text-slate-200 p-2 rounded border border-borderClr self-start max-w-[90%]';
        msgDiv.innerHTML = text.replace(/\n/g, '<br>');
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendChatMessage() {
        const msg = chatInput.value.trim();
        if(!msg) return;
        
        appendChatMessage('user', msg);
        chatInput.value = '';
        
        document.getElementById('chatWelcomeMsg')?.remove();
        
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'text-slate-400 italic text-[9px] mt-1';
        loadingDiv.innerText = 'Gemini Civil AI está pensando...';
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mensaje: msg,
                    historial: chatHistory,
                    partidas: budgetItems
                })
            });
            const data = await response.json();
            
            document.getElementById(loadingId)?.remove();
            
            if(response.ok && data.status === 'success') {
                appendChatMessage('ai', data.respuesta);
                chatHistory.push({role: 'user', content: msg});
                chatHistory.push({role: 'assistant', content: data.respuesta});
                
                let tableChanged = false;
                if(data.acciones && data.acciones.length > 0) {
                    data.acciones.forEach(accion => {
                        if(accion.tipo === 'añadir' && accion.partida) {
                            if (currentUser.plan !== 'pro' && budgetItems.length >= 10) {
                                appendChatMessage('ai', 'Advertencia: No pude añadir más partidas porque alcanzaste el límite de 10 partidas de tu Plan Free.');
                                return;
                            }
                            addBudgetItem(accion.partida);
                            tableChanged = true;
                        } else if(accion.tipo === 'eliminar') {
                            const idx = budgetItems.findIndex(i => i.codigo === accion.codigo);
                            if(idx > -1) {
                                budgetItems.splice(idx, 1);
                                tableChanged = true;
                            }
                        } else if(accion.tipo === 'modificar') {
                            const item = budgetItems.find(i => i.codigo === accion.codigo);
                            if(item) {
                                item.cantidad = parseFloat(accion.nueva_cantidad);
                                tableChanged = true;
                            }
                        }
                    });
                }
                if(tableChanged) renderTable();
            } else {
                appendChatMessage('ai', 'Error: ' + (data.detail || 'Fallo al procesar'));
            }
        } catch(error) {
            document.getElementById(loadingId)?.remove();
            appendChatMessage('ai', 'Ocurrió un error de red al contactar al asistente.');
            console.error(error);
        }
    }

    btnSendChat.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if(e.key === 'Enter') sendChatMessage();
    });

    // === 8. AUTOCOMPLETE BUSCADOR DE CATÁLOGO ===
    let searchTimeout;
    catalogSearchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        if (query.length < 2) {
            catalogSearchResults.classList.add('hidden');
            return;
        }

        searchTimeout = setTimeout(async () => {
            try {
                const res = await fetch(`/api/catalogo?q=${encodeURIComponent(query)}`);
                const partidas = await res.json();
                
                catalogSearchResults.innerHTML = '';
                if (partidas.length === 0) {
                    catalogSearchResults.innerHTML = '<div class="p-3 text-slate-500 text-xs italic">No se encontraron partidas.</div>';
                } else {
                    partidas.forEach(p => {
                        const div = document.createElement('div');
                        div.className = 'p-3 hover:bg-slate-800 border-b border-borderClr/60 cursor-pointer transition-colors text-xs flex justify-between items-center';
                        div.innerHTML = `
                            <div class="flex-1 pr-4">
                                <span class="font-bold text-accentBlue block">${p.codigo}</span>
                                <span class="text-white block font-semibold truncate max-w-md" title="${p.descripcion}">${p.descripcion}</span>
                            </div>
                            <div class="text-right shrink-0">
                                <span class="text-slate-400 block">${p.unidad}</span>
                                <span class="text-emerald-400 font-bold block">$${p.precio_usd.toFixed(2)}</span>
                            </div>
                        `;
                        div.addEventListener('click', () => {
                            // Validar límite para Free
                            if (currentUser.plan !== 'pro' && budgetItems.length >= 10) {
                                alert('Límite del Plan Free alcanzado (máx 10 partidas). Por favor actualice a Pro.');
                                return;
                            }
                            
                            addBudgetItem({
                                codigo: p.codigo,
                                descripcion: p.descripcion,
                                unidad: p.unidad,
                                precio_usd: p.precio_usd,
                                cantidad: 1.0 // Por defecto
                            });
                            renderTable();
                            catalogSearchInput.value = '';
                            catalogSearchResults.classList.add('hidden');
                        });
                        catalogSearchResults.appendChild(div);
                    });
                }
                catalogSearchResults.classList.remove('hidden');
            } catch (err) {
                console.error(err);
            }
        }, 200);
    });

    // Ocultar resultados de búsqueda al hacer clic afuera
    document.addEventListener('click', (e) => {
        if (!catalogSearchInput.contains(e.target) && !catalogSearchResults.contains(e.target)) {
            catalogSearchResults.classList.add('hidden');
        }
    });

    // === 9. GESTIÓN DE TABLA Y OPERACIONES DEL PRESUPUESTO ===
    function addBudgetItem(item) {
        const existingItem = budgetItems.find(i => i.codigo === item.codigo && i.descripcion === item.descripcion);
        if (existingItem) {
            existingItem.cantidad = parseFloat(existingItem.cantidad) + parseFloat(item.cantidad);
        } else {
            budgetItems.push({
                id: Date.now().toString() + Math.random().toString(36).substring(2, 5),
                codigo: item.codigo,
                descripcion: item.descripcion,
                unidad: item.unidad,
                precio_usd: parseFloat(item.precio_usd || 0),
                cantidad: parseFloat(item.cantidad)
            });
        }
    }

    window.removeBudgetItem = function(id) {
        budgetItems = budgetItems.filter(i => i.id !== id);
        renderTable();
    };

    window.openEditModal = function(id) {
        const item = budgetItems.find(i => i.id === id);
        if (item) {
            document.getElementById('editItemId').value = item.id;
            document.getElementById('editItemDesc').value = item.descripcion;
            document.getElementById('editItemUnidad').value = item.unidad;
            document.getElementById('editItemCantidad').value = item.cantidad;
            document.getElementById('editItemPrecio').value = item.precio_usd;
            editModal.classList.remove('hidden');
        }
    };

    window.closeEditModal = () => editModal.classList.add('hidden');

    document.getElementById('btnSaveEdit').addEventListener('click', () => {
        const id = document.getElementById('editItemId').value;
        const item = budgetItems.find(i => i.id === id);
        if (item) {
            item.descripcion = document.getElementById('editItemDesc').value;
            item.unidad = document.getElementById('editItemUnidad').value;
            item.cantidad = parseFloat(document.getElementById('editItemCantidad').value) || 0;
            item.precio_usd = parseFloat(document.getElementById('editItemPrecio').value) || 0;
            renderTable();
        }
        closeEditModal();
    });

    window.updateQty = function(id, qty) {
        const item = budgetItems.find(i => i.id === id);
        if (item) {
            item.cantidad = parseFloat(qty) || 0;
            updateRowSubtotals(id);
            updateTotals();
        }
    };

    function updateRowSubtotals(id) {
        const item = budgetItems.find(i => i.id === id);
        if (item) {
            const subUSD = item.cantidad * item.precio_usd;
            const subVES = subUSD * bcvRate;
            const elSubUsd = document.getElementById(`subusd-${id}`);
            const elSubVes = document.getElementById(`subves-${id}`);
            if (elSubUsd) elSubUsd.textContent = formatCurrency(subUSD);
            if (elSubVes) elSubVes.textContent = formatCurrency(subVES);
        }
    }

    function getCategory(item) {
        let codigo = (item.codigo || '').toUpperCase();
        if (codigo.startsWith('E-1') || codigo.startsWith('E-2')) return 'Infraestructura';
        if (codigo.startsWith('E-3')) return 'Superestructura';
        if (codigo.startsWith('E-5')) return 'Instalaciones Eléctricas';
        if (codigo.startsWith('E-6')) return 'Instalaciones Sanitarias';
        if (codigo.startsWith('E-7') || codigo.startsWith('E-8')) return 'Instalaciones Mecánicas';
        if (codigo.startsWith('I-9')) return 'Gestión de Calidad';
        return 'Otros';
    }

    function renderTable() {
        tableBody.innerHTML = '';
        
        // Actualizar indicadores del límite en la UI
        updateUIRestrictions();

        if (budgetItems.length === 0) {
            btnListaMateriales.disabled = true;
            btnListaMateriales.classList.add('opacity-50', 'cursor-not-allowed');
            updateTotals();
            return;
        }

        btnListaMateriales.disabled = false;
        btnListaMateriales.classList.remove('opacity-50', 'cursor-not-allowed');

        const showCosts = showCostsCheckbox.checked ? 'visible' : 'hidden';

        const categories = {
            'Infraestructura': [],
            'Superestructura': [],
            'Instalaciones Eléctricas': [],
            'Instalaciones Sanitarias': [],
            'Instalaciones Mecánicas': [],
            'Otros': []
        };

        budgetItems.forEach(item => {
             const cat = getCategory(item);
             if(!categories[cat]) categories[cat] = [];
             categories[cat].push(item);
        });

        for (const [catName, items] of Object.entries(categories)) {
            if (items.length === 0) continue;
            
            // Fila cabecera de la categoría
            const catTr = document.createElement('tr');
            catTr.className = 'bg-slate-800/80 font-bold text-white text-[11px]';
            catTr.innerHTML = `<td colspan="8" class="py-2 px-3 border-y border-borderClr uppercase">${catName}</td>`;
            tableBody.appendChild(catTr);

            items.forEach(item => {
                const subUSD = item.cantidad * item.precio_usd;
                const subVES = subUSD * bcvRate;
                
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-700/40 transition-colors group text-slate-300';
                tr.innerHTML = `
                    <td class="py-1.5 px-3 border-r border-borderClr/60">${item.codigo}</td>
                    <td class="py-1.5 px-3 border-r border-borderClr/60 truncate max-w-[240px]" title="${item.descripcion}">${item.descripcion}</td>
                    <td class="py-1.5 px-3 border-r border-borderClr/60 text-center">${item.unidad}</td>
                    <td class="py-1.5 px-3 border-r border-borderClr/60 text-center p-0">
                        <input type="number" step="0.01" min="0" value="${item.cantidad}" oninput="updateQty('${item.id}', this.value)" class="w-full h-full bg-transparent text-center focus:outline-none focus:bg-slate-800 py-1 font-semibold text-white">
                    </td>
                    <td class="py-1.5 px-3 border-r border-borderClr/60 text-right cost-col" style="visibility: ${showCosts}">$${formatCurrency(item.precio_usd)}</td>
                    <td class="py-1.5 px-3 border-r border-borderClr/60 text-right font-semibold cost-col" style="visibility: ${showCosts}">$<span id="subusd-${item.id}">${formatCurrency(subUSD)}</span></td>
                    <td class="py-1.5 px-3 border-r border-borderClr/60 text-right font-semibold text-accentBlue cost-col" style="visibility: ${showCosts}">Bs.<span id="subves-${item.id}">${formatCurrency(subVES)}</span></td>
                    <td class="py-1.5 px-3 text-center flex justify-center gap-1.5">
                        <button onclick="openEditModal('${item.id}')" class="text-slate-400 hover:text-accentBlue transition-colors" title="Modificar Partida">
                            <i class="fa-solid fa-pen"></i>
                        </button>
                        <button onclick="removeBudgetItem('${item.id}')" class="text-slate-400 hover:text-accentRed transition-colors" title="Eliminar Partida">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                `;
                tableBody.appendChild(tr);
            });
        }

        updateTotals();
    }

    function updateTotals() {
        let tUSD = 0;
        budgetItems.forEach(item => {
            tUSD += (item.cantidad * item.precio_usd);
            updateRowSubtotals(item.id);
        });
        const tVES = tUSD * bcvRate;
        totalUSDDisplay.textContent = formatCurrency(tUSD);
        totalVESDisplay.textContent = formatCurrency(tVES);
        totalPartidasDisplay.textContent = budgetItems.length;
    }

    // Escuchar el cambio en la tasa BCV
    bcvRateInput.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        if (!isNaN(val) && val > 0) {
            bcvRate = val;
            updateTotals();
            renderTable();
        }
    });

    // Escuchar checkbox de mostrar costos
    showCostsCheckbox.addEventListener('change', (e) => {
        const cols = document.querySelectorAll('.cost-col');
        cols.forEach(col => {
            col.style.visibility = e.target.checked ? 'visible' : 'hidden';
        });
    });

    // Botón Limpiar/Nuevo presupuesto
    btnNuevoPresupuesto.addEventListener('click', () => {
        if (confirm('¿Está seguro de limpiar todo el presupuesto y empezar uno nuevo?')) {
            budgetItems = [];
            renderTable();
            if (btnEliminarImagen) btnEliminarImagen.click();
        }
    });

    // === 10. GENERACIÓN DE REPORTES PDF Y APUs ===
    
    // PDF de Presupuesto (jsPDF Cliente)
    btnGenerarPDF.addEventListener('click', async () => {
        if (budgetItems.length === 0) {
            alert("No hay partidas para generar el reporte PDF.");
            return;
        }

        // Límite del plan Free (máximo 65 partidas para generar reporte PDF)
        if (currentUser.plan !== 'pro' && budgetItems.length > 65) {
            alert("Su Plan Free tiene un límite de hasta 65 partidas para descargar presupuestos en PDF. Por favor actualice a Pro.");
            return;
        }
        
        showLoading('Generando documento PDF de presupuesto...');
        try {
            const payload = {
                items: budgetItems,
                tasa_bcv: bcvRate,
                incluir_imagen: true,
                datos_cliente: {
                    nombre: clientNombre.value.trim() || 'N/D',
                    telefono: clientTelefono.value.trim() || 'N/D',
                    proyecto: editorProjectTitle.value.trim() || 'Proyecto de Obra',
                    ubicacion: clientUbicacion.value.trim() || 'N/D'
                },
                datos_profesional: getProfessionalConfig()
            };

            const res = await fetch('/api/presupuesto/pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Presupuesto_${payload.datos_cliente.proyecto.replace(/\s+/g, '_')}.pdf`;
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                const errData = await res.json();
                alert('Error al generar PDF: ' + (errData.detail || 'Fallo desconocido'));
            }
        } catch (e) {
            console.error(e);
            alert('Error de conexión al exportar PDF.');
        } finally {
            hideLoading();
        }
    });

    // Reporte detallado de APUs (FastAPI PDF backend)
    btnGenerarApuPDF.addEventListener('click', async () => {
        if (budgetItems.length === 0) {
            alert('Añada partidas al presupuesto primero.');
            return;
        }

        showLoading('Generando Análisis de Precios Unitarios en PDF...');
        try {
            const payload = {
                items: budgetItems,
                tasa_bcv: bcvRate,
                datos_cliente: {
                    nombre: clientNombre.value.trim() || 'N/D',
                    telefono: clientTelefono.value.trim() || 'N/D',
                    proyecto: editorProjectTitle.value.trim() || 'Proyecto de Obra',
                    ubicacion: clientUbicacion.value.trim() || 'N/D'
                },
                datos_profesional: getProfessionalConfig()
            };

            const res = await fetch('/api/presupuesto/apu-pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Analisis_Precios_Unitarios_${payload.datos_cliente.proyecto.replace(/\s+/g, '_')}.pdf`;
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                const errData = await res.json();
                alert('Error al generar APUs: ' + (errData.detail || 'Fallo desconocido'));
            }
        } catch (e) {
            console.error(e);
            alert('Error de conexión al exportar APUs.');
        } finally {
            hideLoading();
        }
    });

    // Memoria Descriptiva con IA
    btnGenerarMemoria.addEventListener('click', async () => {
        if (budgetItems.length === 0) {
            alert('Añada algunas partidas al presupuesto primero.');
            return;
        }
        
        showLoading('Generando Memoria Descriptiva mediante IA (Redactando PDF)...');
        try {
            const payload = {
                datos_cliente: {
                    nombre: clientNombre.value.trim() || 'N/D',
                    telefono: clientTelefono.value.trim() || 'N/D',
                    proyecto: editorProjectTitle.value.trim() || 'Proyecto de Obra',
                    ubicacion: clientUbicacion.value.trim() || 'N/D'
                },
                items: budgetItems,
                datos_profesional: getProfessionalConfig()
            };
            
            const res = await fetch('/api/memoria', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Memoria_Descriptiva_${payload.datos_cliente.proyecto.replace(/\s+/g, '_')}.pdf`;
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                const errorData = await res.json();
                alert(`Error al generar la Memoria: ${errorData.message || 'Desconocido'}`);
            }
        } catch (error) {
            alert(`Fallo de conexión al generar Memoria: ${error}`);
        } finally {
            hideLoading();
        }
    });

    // Lista de Materiales (BOM) consolidada
    window.closeBomModal = () => bomModal.classList.add('hidden');

    btnListaMateriales.addEventListener('click', async () => {
        if (budgetItems.length === 0) return;
        
        showLoading('Generando lista consolidada de materiales...');
        try {
            const payload = { items: budgetItems.map(i => ({ codigo: i.codigo, cantidad: i.cantidad })) };
            const res = await fetch('/api/bom', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            hideLoading();
            if (res.ok && data.status === 'success') {
                bomTableBody.innerHTML = '';
                if (data.bom.length > 0) {
                    data.bom.sort((a,b) => a.codigo.localeCompare(b.codigo)).forEach(mat => {
                        const tr = document.createElement('tr');
                        tr.className = 'hover:bg-slate-800 transition-colors text-slate-300';
                        tr.innerHTML = `
                            <td class="py-2 px-3 border-r border-borderClr/60 font-semibold text-accentOrange">${mat.codigo}</td>
                            <td class="py-2 px-3 border-r border-borderClr/60">${mat.descripcion}</td>
                            <td class="py-2 px-3 border-r border-borderClr/60 text-center">${mat.unidad}</td>
                            <td class="py-2 px-3 text-right font-bold text-white">${formatCurrency(mat.cantidad)}</td>
                        `;
                        bomTableBody.appendChild(tr);
                    });
                } else {
                    bomTableBody.innerHTML = '<tr><td colspan="4" class="py-4 text-center text-slate-500">No hay materiales asociados a estas partidas.</td></tr>';
                }
                bomModal.classList.remove('hidden');
            } else {
                alert('Error al consolidar la lista: ' + (data.detail || 'Fallo desconocido'));
            }
        } catch (e) {
            hideLoading();
            alert('Fallo de conexión al generar BOM: ' + e);
        }
    });

    // === 12. CONFIGURACIÓN DEL EMISOR, SOPORTE Y ADMIN DASHBOARD ===
    
    // Profesional / Emisor
    window.openProfModal = function() {
        document.getElementById('profEmpresa').value = localStorage.getItem('prof_empresa') || '';
        document.getElementById('profNombre').value = localStorage.getItem('prof_nombre') || '';
        
        const storedLogo = localStorage.getItem('prof_logo');
        if (storedLogo) {
            document.getElementById('profLogoPreview').src = storedLogo;
            document.getElementById('profLogoPreviewContainer').classList.remove('hidden');
        } else {
            document.getElementById('profLogoPreviewContainer').classList.add('hidden');
        }
        document.getElementById('profModal').classList.remove('hidden');
    };
    
    window.closeProfModal = function() {
        document.getElementById('profModal').classList.add('hidden');
    };
    
    window.clearProfLogo = function() {
        document.getElementById('profLogoFile').value = '';
        localStorage.removeItem('prof_logo');
        document.getElementById('profLogoPreview').src = '';
        document.getElementById('profLogoPreviewContainer').classList.add('hidden');
    };
    
    window.saveProfConfig = function() {
        const empresa = document.getElementById('profEmpresa').value.trim();
        const profesional = document.getElementById('profNombre').value.trim();
        
        localStorage.setItem('prof_empresa', empresa);
        localStorage.setItem('prof_nombre', profesional);
        
        const logoFile = document.getElementById('profLogoFile').files[0];
        if (logoFile) {
            const reader = new FileReader();
            reader.onload = function(e) {
                localStorage.setItem('prof_logo', e.target.result);
                closeProfModal();
                alert("Configuración del emisor guardada con éxito.");
            };
            reader.readAsDataURL(logoFile);
        } else {
            closeProfModal();
            alert("Configuración del emisor guardada con éxito.");
        }
    };
    
    function getProfessionalConfig() {
        return {
            empresa: localStorage.getItem('prof_empresa') || 'CONSTRUCCIONES JROBOTWEB',
            profesional: localStorage.getItem('prof_nombre') || 'Firma Autorizada',
            civ: '',
            logo_base64: localStorage.getItem('prof_logo') || ''
        };
    }
    
    // Soporte y Sugerencias
    window.openSupportModal = function() {
        document.getElementById('supportMensaje').value = '';
        document.getElementById('supportTipo').value = 'sugerencia';
        document.getElementById('supportModal').classList.remove('hidden');
    };
    
    window.closeSupportModal = function() {
        document.getElementById('supportModal').classList.add('hidden');
    };
    
    window.sendSupportReport = async function() {
        const tipo = document.getElementById('supportTipo').value;
        const mensaje = document.getElementById('supportMensaje').value.trim();
        
        if (!mensaje) {
            alert("Por favor escribe tu mensaje o sugerencia.");
            return;
        }
        
        showLoading("Enviando reporte...");
        try {
            const res = await fetch('/api/sugerencias', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tipo, mensaje })
            });
            
            if (res.ok) {
                closeSupportModal();
                alert("¡Muchas gracias! Tu mensaje ha sido enviado al equipo técnico.");
            } else {
                alert("Error al enviar reporte.");
            }
        } catch (e) {
            console.error(e);
            alert("Error de conexión al enviar.");
        } finally {
            hideLoading();
        }
    };
    
    // Admin Dashboard
    let adminActiveTab = 'users';
    
    window.openAdminModal = function() {
        document.getElementById('adminModal').classList.remove('hidden');
        switchAdminTab('users');
    };
    
    window.closeAdminModal = function() {
        document.getElementById('adminModal').classList.add('hidden');
        verificarSesion(); // Recargar el estado por si acaso cambió el plan del admin
    };
    
    window.switchAdminTab = function(tab) {
        adminActiveTab = tab;
        const usersBtn = document.getElementById('tabUsersBtn');
        const sugsBtn = document.getElementById('tabSugsBtn');
        const usersDiv = document.getElementById('adminTabUsers');
        const sugsDiv = document.getElementById('adminTabSugs');
        
        if (tab === 'users') {
            usersBtn.className = 'px-3 py-1.5 rounded font-bold text-xs bg-accentPurple text-white';
            sugsBtn.className = 'px-3 py-1.5 rounded font-bold text-xs bg-slate-800 text-slate-300 hover:text-white';
            usersDiv.classList.remove('hidden');
            sugsDiv.classList.add('hidden');
            loadAdminUsers();
        } else {
            sugsBtn.className = 'px-3 py-1.5 rounded font-bold text-xs bg-accentPurple text-white';
            usersBtn.className = 'px-3 py-1.5 rounded font-bold text-xs bg-slate-800 text-slate-300 hover:text-white';
            sugsDiv.classList.remove('hidden');
            usersDiv.classList.add('hidden');
            loadAdminSugerencias();
        }
    };
    
    async function loadAdminUsers() {
        document.getElementById('adminUsersTableBody').innerHTML = '<tr><td colspan="6" class="py-4 text-center text-slate-500">Cargando usuarios...</td></tr>';
        document.getElementById('adminEditPlanForm').classList.add('hidden');
        
        try {
            const res = await fetch('/api/admin/users');
            const data = await res.json();
            if (res.ok && data.users) {
                const tbody = document.getElementById('adminUsersTableBody');
                tbody.innerHTML = '';
                
                data.users.forEach(u => {
                    const tr = document.createElement('tr');
                    tr.className = 'border-b border-borderClr/60 hover:bg-slate-800/40 transition-colors';
                    
                    const expiry = u.current_period_end ? u.current_period_end.split('T')[0] : 'Indefinido / N/A';
                    const planBadge = u.plan === 'pro' ? '<span class="bg-purple-500/20 text-purple-400 border border-purple-500/30 px-2 py-0.5 rounded text-[9px] uppercase font-bold">Pro</span>' : '<span class="bg-slate-700 text-slate-300 border border-slate-600 px-2 py-0.5 rounded text-[9px] uppercase font-bold">Free</span>';
                    const statusBadge = u.status === 'active' ? '<span class="text-emerald-400">Activo</span>' : '<span class="text-red-400">Inactivo / Exp</span>';
                    
                    const paymentDetail = u.plan === 'pro' ? `<div class="text-[9px] text-slate-400 mt-0.5 font-medium"><i class="fa-solid fa-credit-card text-accentBlue mr-1"></i>${u.metodo_pago || 'Manual'} (${u.referencia_pago || 'Sin Ref'})</div>` : '';
                    const budgetsCount = `<div class="text-[9px] text-accentOrange font-medium mt-0.5"><i class="fa-solid fa-folder-open mr-1"></i>Creados: ${u.total_presupuestos || 0}</div>`;
                    
                    tr.innerHTML = `
                        <td class="px-4 py-3 font-semibold text-white">
                            ${u.email}
                            ${paymentDetail}
                        </td>
                        <td class="px-4 py-3">
                            ${u.nombre}
                            ${budgetsCount}
                        </td>
                        <td class="px-4 py-3">${planBadge}</td>
                        <td class="px-4 py-3">${statusBadge}</td>
                        <td class="px-4 py-3 text-slate-400">${expiry}</td>
                        <td class="px-4 py-3 text-center">
                            <button onclick="editUserPlan('${u.id}', '${u.email}', '${u.plan}', '${u.status}', '${u.current_period_end || ''}')" class="bg-slate-800 hover:bg-slate-700 text-accentBlue border border-borderClr px-2.5 py-1 rounded text-[10px] transition-colors"><i class="fa-solid fa-pen"></i> Asignar Plan</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                alert("Error al cargar usuarios.");
            }
        } catch (e) {
            console.error(e);
        }
    }
    
    window.editUserPlan = function(id, email, plan, status, expiry) {
        document.getElementById('adminEditUserId').value = id;
        document.getElementById('adminEditUserEmail').textContent = email;
        document.getElementById('adminEditPlan').value = plan || 'free';
        document.getElementById('adminEditStatus').value = status || 'active';
        document.getElementById('adminEditExpiry').value = expiry ? expiry.split('T')[0] : '';
        document.getElementById('adminEditPlanForm').classList.remove('hidden');
        document.getElementById('adminEditPlanForm').scrollIntoView({ behavior: 'smooth' });
    };
    
    window.cancelAdminEditPlan = function() {
        document.getElementById('adminEditPlanForm').classList.add('hidden');
    };
    
    window.saveAdminUserPlan = async function() {
        const id = document.getElementById('adminEditUserId').value;
        const plan = document.getElementById('adminEditPlan').value;
        const status = document.getElementById('adminEditStatus').value;
        const expiry = document.getElementById('adminEditExpiry').value;
        
        showLoading("Actualizando plan de usuario...");
        try {
            const res = await fetch('/api/admin/users/update-plan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: parseInt(id),
                    plan: plan,
                    status: status,
                    current_period_end: expiry || null
                })
            });
            
            if (res.ok) {
                document.getElementById('adminEditPlanForm').classList.add('hidden');
                alert("Plan de usuario actualizado correctamente.");
                loadAdminUsers();
            } else {
                alert("Error al guardar cambios de plan.");
            }
        } catch (e) {
            console.error(e);
            alert("Error de conexión al actualizar.");
        } finally {
            hideLoading();
        }
    };
    
    async function loadAdminSugerencias() {
        const container = document.getElementById('adminSugsList');
        container.innerHTML = '<p class="text-center text-slate-500 text-xs py-4">Cargando sugerencias...</p>';
        
        try {
            const res = await fetch('/api/admin/sugerencias');
            const data = await res.json();
            if (res.ok && data.sugerencias) {
                container.innerHTML = '';
                if (data.sugerencias.length === 0) {
                    container.innerHTML = '<p class="text-center text-slate-500 text-xs py-4">No se han registrado reportes ni sugerencias.</p>';
                    return;
                }
                
                data.sugerencias.forEach(s => {
                    const div = document.createElement('div');
                    div.className = 'p-4 border border-borderClr rounded-lg bg-bgMain flex flex-col gap-2';
                    
                    const badge = s.tipo === 'sugerencia' ? '<span class="bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded text-[8px] uppercase font-bold self-start">Sugerencia</span>' : '<span class="bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded text-[8px] uppercase font-bold self-start">Soporte Técnico</span>';
                    const dateStr = s.created_at ? s.created_at.replace('T', ' ').substring(0, 19) : '';
                    
                    div.innerHTML = `
                        <div class="flex justify-between items-start">
                            <div class="flex flex-col">
                                <span class="font-bold text-xs text-white">${s.nombre} (${s.email})</span>
                                <span class="text-[9px] text-slate-400">${dateStr}</span>
                            </div>
                            ${badge}
                        </div>
                        <p class="text-[11px] text-slate-300 leading-relaxed bg-bgPanel/40 p-2.5 rounded border border-borderClr/40 font-mono resize-none">${s.mensaje}</p>
                    `;
                    container.appendChild(div);
                });
            } else {
                alert("Error al cargar sugerencias.");
            }
        } catch (e) {
            console.error(e);
        }
    }

    // === 11. HELPERS DE CARGA / LOADERS ===
    function showLoading(msg) {
        loadingText.textContent = msg || 'Procesando...';
        loadingOverlay.classList.remove('hidden');
        loadingOverlay.classList.add('flex');
    }

    function hideLoading() {
        loadingOverlay.classList.add('hidden');
        loadingOverlay.classList.remove('flex');
    }
    
    // Registrar el manejador de archivo para previsualización inmediata de logo
    const profLogoFile = document.getElementById('profLogoFile');
    if (profLogoFile) {
        profLogoFile.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(evt) {
                    document.getElementById('profLogoPreview').src = evt.target.result;
                    document.getElementById('profLogoPreviewContainer').classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            }
        });
    }
});
