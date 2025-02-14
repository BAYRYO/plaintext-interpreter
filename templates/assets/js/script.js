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