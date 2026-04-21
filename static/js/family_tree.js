const modal = document.getElementById('member-modal');

if (modal) {
    const title = document.getElementById('member-modal-title');
    const generation = document.getElementById('member-modal-generation');
    const years = document.getElementById('member-modal-years');
    const hometown = document.getElementById('member-modal-hometown');
    const spouse = document.getElementById('member-modal-spouse');
    const bio = document.getElementById('member-modal-bio');

    const fillAndOpenModal = (source) => {
        title.textContent = source.dataset.memberName || '';
        generation.textContent = source.dataset.memberGeneration || '';
        years.textContent = source.dataset.memberYears || '';
        hometown.textContent = source.dataset.memberHometown || '';
        spouse.textContent = source.dataset.memberSpouse || '';
        bio.textContent = source.dataset.memberBio || '';
        modal.hidden = false;
    };

    // Event delegation keeps click working even if layout/template changes.
    document.addEventListener('click', (event) => {
        const target = event.target.closest('[data-member-name]');
        if (!target) {
            return;
        }
        fillAndOpenModal(target);
    });

    modal.querySelectorAll('[data-close-modal]').forEach((element) => {
        element.addEventListener('click', () => {
            modal.hidden = true;
        });
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            modal.hidden = true;
        }
    });
}
