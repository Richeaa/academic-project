document.addEventListener('DOMContentLoaded', function () {
  const path = window.location.pathname;
  
  const navItems = [
    { id: 'dashboard-link', url: '/dashboard/' },
    { id: 'lecturer-link', url: '/lecturer/' },
    ];

    navItems.forEach(item => {
    const el = document.getElementById(item.id);
    if (el) {
      const pageUrl = el.dataset.pageUrl || item.url;
      if (path === pageUrl) {
        const div = el.querySelector('div');
        if (div) {
          div.classList.add(
            'bg-sky-300/20',
            'text-blue-700',
            'transition',
            'duration-100',
            'ease-in-out'
          );
        }
      }
    }
  });
  
  const hamburger = document.getElementById('hamburger');
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('main-content');
  const profilebutton = document.getElementById('profile-button');
  const dropdownmenuprofile = document.getElementById('dropdown-menu-profile');


  profilebutton.addEventListener('click', function (e) {
      e.stopPropagation(); 
      dropdownmenuprofile.classList.toggle('hidden');
    });

  document.addEventListener('click', function (e) {
      if (!profilebutton.contains(e.target) && !dropdownmenuprofile.contains(e.target)) {
        dropdownmenuprofile.classList.add('hidden');
    }
  });

  function handleSidebar() {
    const isMobile = window.innerWidth < 1024; 
    
    if (isMobile) {
      sidebar.classList.add('-translate-x-full', 'z-50'); 
      sidebar.classList.remove('z-20');
      mainContent.classList.remove('ml-72');
    } else {
      sidebar.classList.remove('z-50');
      sidebar.classList.add('z-20');
      if (!sidebar.classList.contains('-translate-x-full')) {
        mainContent.classList.add('ml-72');
      } else {
        mainContent.classList.remove('ml-72');
      }
    }
  }

  handleSidebar();

  window.addEventListener('resize', handleSidebar);

  hamburger.addEventListener('click', function () {
    const isHidden = sidebar.classList.contains('-translate-x-full');
    
    sidebar.classList.toggle('-translate-x-full');

    if (window.innerWidth >= 1024) {
      if (isHidden) {
        mainContent.classList.add('ml-72');
      } else {
        mainContent.classList.remove('ml-72');
      }
    }
  });
});


function toggleDropdown() {
    const content = document.getElementById('dropdown-content');
    const arrow = document.getElementById('dropdown-arrow');
    content.classList.toggle('hidden');
    arrow.classList.toggle('rotate-180');
}