const modal = document.getElementById('member-modal');

if (modal) {
    const title = document.getElementById('member-modal-title');
    const generation = document.getElementById('member-modal-generation');
    const years = document.getElementById('member-modal-years');
    const hometown = document.getElementById('member-modal-hometown');
    const spouse = document.getElementById('member-modal-spouse');
    const bio = document.getElementById('member-modal-bio');

    document.querySelectorAll('.tree-person').forEach((button) => {
        button.addEventListener('click', () => {
            title.textContent = button.dataset.memberName || '';
            generation.textContent = button.dataset.memberGeneration || '';
            years.textContent = button.dataset.memberYears || '';
            hometown.textContent = button.dataset.memberHometown || '';
            spouse.textContent = button.dataset.memberSpouse || '';
            bio.textContent = button.dataset.memberBio || '';
            modal.hidden = false;
        });
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
