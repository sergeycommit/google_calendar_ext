document.addEventListener('DOMContentLoaded', function () {
    const quickAddInput = document.getElementById('quick-add');

    // Handle ⌘+K / Ctrl+K shortcut
    document.addEventListener('keydown', function (e) {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            quickAddInput.focus();
        }
    });

    // Simulate data loading transition
    setTimeout(() => {
        const skeletons = document.querySelectorAll('.event-item.skeleton');
        const eventList = document.querySelector('.event-list');

        // In a real app, we would fetch data and replace skeletons
        // For now, we'll just demonstrate the transition
        skeletons.forEach(s => s.classList.remove('skeleton'));

        // Example of filling data (simulated)
        const titles = ['AI Workgroup', 'Team Birthday', 'Project Sync'];
        const times = ['13:00', '15:30', '17:00'];

        const skeletonTitles = document.querySelectorAll('.event-title-skeleton');
        const skeletonTimes = document.querySelectorAll('.event-time-skeleton');

        skeletonTitles.forEach((t, i) => {
            t.textContent = titles[i];
            t.style.background = 'none';
        });

        skeletonTimes.forEach((t, i) => {
            t.textContent = times[i];
            t.style.background = 'none';
        });
    }, 2000);
});
