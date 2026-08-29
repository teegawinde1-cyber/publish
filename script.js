document.addEventListener('DOMContentLoaded', () => {
    loadAds(); // Charger les annonces depuis le serveur au démarrage

    const modal = document.getElementById("adModal");
    const aiModal = document.getElementById("aiModal");
    const btn = document.getElementById("addAdBtn");
    
    const span = document.getElementsByClassName("close")[0];
    const spanAi = document.getElementsByClassName("close-ai")[0];
    
    const radios = document.getElementsByName("visibility");
    const paymentButtons = document.getElementById("paymentButtons");
    const submitBtn = document.getElementById("submitBtn");

    // Temporaire data de l'annonce en cours
    let currentAdData = null;

    btn.onclick = () => modal.style.display = "block";
    span.onclick = () => modal.style.display = "none";
    spanAi.onclick = () => aiModal.style.display = "none";

    radios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'vip') {
                paymentButtons.classList.remove('hidden');
                submitBtn.classList.add('hidden');
            } else {
                paymentButtons.classList.add('hidden');
                submitBtn.classList.remove('hidden');
                submitBtn.textContent = "Publier (Gratuit)";
            }
        });
    });

    // Formulaire d'annonce
    document.getElementById("adForm").addEventListener("submit", async function(e) {
        e.preventDefault();
        
        const visibility = document.querySelector('input[name="visibility"]:checked').value;
        const adData = {
            title: document.getElementById("adTitle").value,
            description: document.getElementById("adDesc").value,
            link: document.getElementById("adLink").value,
            is_vip: false
        };

        if(visibility === 'free') {
            await publishAd(adData);
            modal.style.display = "none";
            this.reset();
            alert("Votre annonce gratuite a été publiée avec succès !");
        }
    });

    // Gestion du bouton de validation dans le chat IA
    document.getElementById("verifyTxBtn").onclick = async function() {
        const input = document.getElementById("txIdInput");
        const txId = input.value.trim();
        if(!txId) return;

        addChatMessage(txId, 'user');
        input.value = '';

        // Simuler la réflexion de l'IA
        setTimeout(async () => {
            const res = await fetch('/api/bot/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({transaction_id: txId})
            });
            const data = await res.json();

            if(data.valid) {
                addChatMessage(data.message + " Je publie votre annonce en VIP !", 'ai');
                
                // Publier avec le VIP
                currentAdData.is_vip = true;
                currentAdData.transaction_id = txId;
                await publishAd(currentAdData);
                
                setTimeout(() => {
                    aiModal.style.display = "none";
                    document.getElementById("adForm").reset();
                }, 2000);
            } else {
                addChatMessage(data.message, 'ai');
            }
        }, 1000);
    };
});

// Appelé quand on clique sur "Orange Money" ou "Wave" dans le modal
function simulatePayment(provider) {
    const title = document.getElementById("adTitle").value;
    const desc = document.getElementById("adDesc").value;
    const link = document.getElementById("adLink").value;

    if (!title || !desc || !link) {
        alert("Veuillez d'abord remplir tous les champs !");
        return;
    }

    // Sauvegarder les données pour les utiliser après le chat
    window.currentAdData = { title, description: desc, link };

    document.getElementById("adModal").style.display = "none";
    document.getElementById("aiModal").style.display = "block";
    
    // Reset chat
    const chatBody = document.getElementById("chatBody");
    // On garde juste les 3 premiers messages
    while(chatBody.children.length > 3) {
        chatBody.removeChild(chatBody.lastChild);
    }
}

function addChatMessage(text, sender) {
    const chatBody = document.getElementById("chatBody");
    const div = document.createElement('div');
    div.className = `message ${sender}-message`;
    div.innerHTML = text;
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
}

// Fonction pour envoyer au serveur
async function publishAd(data) {
    await fetch('/api/ads', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    loadAds();
}

// Fonction pour charger depuis le serveur
async function loadAds() {
    const res = await fetch('/api/ads');
    const ads = await res.json();
    
    const grid = document.getElementById("adsGrid");
    grid.innerHTML = ''; // Nettoyer
    
    ads.forEach(ad => {
        const card = document.createElement('div');
        card.className = `ad-card ${ad.is_vip ? 'vip' : ''}`;
        
        let innerHTML = '';
        if (ad.is_vip) {
            innerHTML += `<div class="badge-vip">★ Recommandé ★</div>`;
        }
        
        innerHTML += `
            <div class="card-inner">
                <h4>${ad.title}</h4>
                <p>${ad.description}</p>
                <a href="${ad.link}" target="_blank" class="btn-link">Accéder au service ➔</a>
            </div>
        `;
        card.innerHTML = innerHTML;
        grid.appendChild(card);
    });
}
