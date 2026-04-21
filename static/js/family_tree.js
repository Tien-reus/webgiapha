const modal = document.getElementById('member-modal');

if (modal) {
    const title = document.getElementById('member-modal-title');
    const birthYear = document.getElementById('member-modal-birth-year');
    const deathYear = document.getElementById('member-modal-death-year');
    const hometown = document.getElementById('member-modal-hometown');
    const father = document.getElementById('member-modal-father');
    const mother = document.getElementById('member-modal-mother');
    const spouse = document.getElementById('member-modal-spouse');
    const occupation = document.getElementById('member-modal-occupation');
    const achievements = document.getElementById('member-modal-achievements');
    const education = document.getElementById('member-modal-education');
    const notes = document.getElementById('member-modal-notes');
    const children = document.getElementById('member-modal-children');

    const textOrDefault = (value, fallback) => value && String(value).trim() ? value : fallback;

    const fillAndOpenModal = (data) => {
        title.textContent = `Người: ${textOrDefault(data.full_name, 'Chưa cập nhật')}`;
        birthYear.textContent = `Năm sinh: ${textOrDefault(data.birth_year, '(chưa ghi trong gia phả)')}`;
        deathYear.textContent = `Năm mất: ${textOrDefault(data.death_year, '(chưa ghi trong gia phả)')}`;
        hometown.textContent = `Quê quán: ${textOrDefault(data.hometown, '(chưa ghi trong gia phả)')}`;
        father.textContent = `Cha: ${textOrDefault(data.father_name, '(chưa ghi trong gia phả)')}`;
        mother.textContent = `Mẹ: ${textOrDefault(data.mother_name, '(chưa ghi trong gia phả)')}`;
        spouse.textContent = `Vợ/chồng: ${textOrDefault(data.spouse_name, '(chưa ghi trong gia phả)')}`;
        occupation.textContent = `Nghề nghiệp: ${textOrDefault(data.occupation, '(chưa ghi trong gia phả)')}`;
        achievements.textContent = `Công danh: ${textOrDefault(data.achievements, '(chưa ghi trong gia phả)')}`;
        education.textContent = `Trình độ: ${textOrDefault(data.education, '(chưa ghi trong gia phả)')}`;
        notes.textContent = `Ghi chú: ${textOrDefault(data.notes, '(chưa ghi trong gia phả)')}`;

        children.innerHTML = '';
        if (Array.isArray(data.children) && data.children.length) {
            data.children.forEach((child) => {
                const li = document.createElement('li');
                const year = child.birth_year ? ` (${child.birth_year})` : '';
                li.textContent = `${child.full_name}${year}`;
                children.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = '(chưa ghi trong gia phả)';
            children.appendChild(li);
        }
        modal.hidden = false;
    };

    // Event delegation keeps click working even if layout/template changes.
    document.addEventListener('click', async (event) => {
        const target = event.target.closest('[data-member-name]');
        if (!target) {
            return;
        }
        const memberId = target.dataset.memberId;
        if (!memberId) {
            return;
        }
        try {
            const response = await fetch(`/members/${memberId}/detail/`);
            if (!response.ok) {
                return;
            }
            const data = await response.json();
            fillAndOpenModal(data);
        } catch (error) {
            // Keep silent to avoid breaking UX if network hiccups.
        }
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
