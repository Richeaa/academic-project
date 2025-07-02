document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');
    
    hamburger.addEventListener('click', function() {
        sidebar.classList.toggle('-translate-x-full');
        overlay.classList.toggle('hidden');
    });

});

function toggleDropdown() {
    const content = document.getElementById('dropdown-content');
    const arrow = document.getElementById('dropdown-arrow');
    content.classList.toggle('hidden');
    arrow.classList.toggle('rotate-180');
}