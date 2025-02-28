document.addEventListener("DOMContentLoaded", () => {
    const toggleButton = document.getElementById('toggle-panneau');
    const panneauArborescence = document.getElementById('panneau-arborescence');

    toggleButton.addEventListener('click', () => {
        panneauArborescence.style.display = panneauArborescence.style.display === 'none' ? 'block' : 'none';
    });
});

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('code').forEach((block) => {
        try {
            const result = hljs.highlightAuto(block.textContent);
            block.classList.add(result.language || 'bash'); // Appliquer le langage détecté ou bash par défaut
        } catch (e) {
            block.classList.add('bash'); // Appliquer bash par défaut
        }
        hljs.highlightElement(block);
    });
});

document.addEventListener("DOMContentLoaded", () => {
    // Ajouter le bouton de copie à tous les blocs pre
    document.querySelectorAll('pre').forEach(pre => {
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.style.width = '30px';  // Définir une largeur fixe
        copyButton.style.height = '30px'; // Définir une hauteur fixe
        copyButton.style.padding = '0';   // Supprimer le padding
        copyButton.style.display = 'flex';// Utiliser flexbox pour centrer l'icône
        copyButton.style.justifyContent = 'center';
        copyButton.style.alignItems = 'center';
        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
        
        copyButton.addEventListener('click', async () => {
            // Récupérer le texte du bloc code
            const code = pre.querySelector('code');
            const text = code.innerText;
            
            try {
                await navigator.clipboard.writeText(text);
                copyButton.innerHTML = '<i class="fas fa-check"></i>';
                copyButton.classList.add('copied');
                
                // Rétablir le bouton après 2 secondes
                setTimeout(() => {
                    copyButton.innerHTML = '<i class="fas fa-copy"></i>';
                    copyButton.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Erreur lors de la copie :', err);
                copyButton.innerHTML = '<i class="fas fa-times"></i>';
                
                setTimeout(() => {
                    copyButton.innerHTML = '<i class="fas fa-copy"></i>';
                }, 2000);
            }
        });
        
        pre.appendChild(copyButton);
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const navigationLinks = document.querySelectorAll('#panneau-arborescence .navigation-list a');
    const sections = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    const panneau = document.getElementById('panneau-arborescence');
    let currentSection = null;
    const headerOffset = 20;

    // Fonction pour faire défiler le panneau de navigation de manière smooth
    function scrollActiveItemIntoView(activeItem, instant = false) {
        if (!activeItem || !panneau) return;

        const panneauRect = panneau.getBoundingClientRect();
        const itemRect = activeItem.getBoundingClientRect();
        
        // Calculer la position centrale souhaitée
        const targetScrollTop = panneau.scrollTop + 
            (itemRect.top - panneauRect.top) - 
            (panneauRect.height / 2) + 
            (itemRect.height / 2);

        // Vérifier les limites de défilement
        const maxScroll = panneau.scrollHeight - panneau.clientHeight;
        const finalScrollTop = Math.max(0, Math.min(targetScrollTop, maxScroll));

        // Appliquer le défilement
        panneau.scrollTo({
            top: finalScrollTop,
            behavior: instant ? 'instant' : 'smooth'
        });
    }

    function updateActiveSection() {
        const scrollPosition = window.scrollY;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        let activeLink = null;

        // Cas spécial pour le haut de la page
        if (scrollPosition <= headerOffset) {
            const firstLink = navigationLinks[0];
            if (firstLink && firstLink !== activeLink) {
                navigationLinks.forEach(link => link.classList.remove('active'));
                firstLink.classList.add('active');
                scrollActiveItemIntoView(firstLink);
                currentSection = firstLink.getAttribute('href').substring(1);
            }
            return;
        }

        // Cas spécial pour le bas de la page
        if (scrollPosition + windowHeight >= documentHeight - 50) {
            const lastLink = navigationLinks[navigationLinks.length - 1];
            if (lastLink && lastLink !== activeLink) {
                navigationLinks.forEach(link => link.classList.remove('active'));
                lastLink.classList.add('active');
                scrollActiveItemIntoView(lastLink);
                currentSection = lastLink.getAttribute('href').substring(1);
            }
            return;
        }

        // Trouver la section actuellement visible
        let bestVisibleSection = null;
        let bestVisibility = 0;

        sections.forEach(section => {
            const rect = section.getBoundingClientRect();
            const visibleHeight = Math.min(rect.bottom, windowHeight) - Math.max(rect.top, 0);
            const visibility = Math.max(0, visibleHeight / rect.height);

            if (visibility > bestVisibility) {
                bestVisibility = visibility;
                bestVisibleSection = section;
            }
        });

        if (bestVisibleSection && bestVisibleSection.id !== currentSection) {
            navigationLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${bestVisibleSection.id}`) {
                    link.classList.add('active');
                    activeLink = link;
                    scrollActiveItemIntoView(link);
                    currentSection = bestVisibleSection.id;
                }
            });
        }
    }

    // Observer pour la détection des sections avec une marge adaptative
    const observerOptions = {
        root: null,
        rootMargin: '-10% 0px -10% 0px',
        threshold: Array.from({ length: 11 }, (_, i) => i / 10) // [0, 0.1, 0.2, ..., 1.0]
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                updateActiveSection();
            }
        });
    }, observerOptions);

    sections.forEach(section => observer.observe(section));

    // Gestion du scroll avec debounce et throttle optimisés
    let scrollTimeout;
    let lastScrollTime = 0;
    const scrollThrottle = 100; // ms

    document.addEventListener('scroll', () => {
        const now = Date.now();

        // Clear le timeout existant
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }

        // Throttle pendant le défilement rapide
        if (now - lastScrollTime >= scrollThrottle) {
            lastScrollTime = now;
            updateActiveSection();
        }

        // Debounce pour la mise à jour finale
        scrollTimeout = setTimeout(() => {
            updateActiveSection();
        }, 150);
    });

    // Gestion du clic sur les liens de navigation
    navigationLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                // Mettre à jour la navigation avant le défilement
                navigationLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
                scrollActiveItemIntoView(link);
                currentSection = targetId;

                // Défilement smooth vers la cible
                const elementPosition = targetElement.offsetTop;
                window.scrollTo({
                    top: elementPosition - headerOffset,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Initialisation avec un délai pour permettre le rendu complet
    setTimeout(() => {
        updateActiveSection();
    }, 100);
});
