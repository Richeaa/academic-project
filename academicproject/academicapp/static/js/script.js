document.addEventListener('DOMContentLoaded', function () {
  const path = window.location.pathname;
  
  const navItems = [
   {
      id: 'dashboard-link',
      match: (p) => p.startsWith('/dashboard/'),
    },
    {
      id: 'studyprogram-link',
      match: (p) => p.startsWith('/studyprogram/'), 
    },
  ];

  navItems.forEach(item => {
    const el = document.getElementById(item.id);
    if (el && item.match(path)) {
      el.addEventListener('click', function (e) {
        e.preventDefault();
      });
      
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
      mainContent.classList.remove('ml-64');
    } else {
      sidebar.classList.remove('z-50');
      sidebar.classList.add('z-20');
      if (!sidebar.classList.contains('-translate-x-full')) {
        mainContent.classList.add('ml-64');
      } else {
        mainContent.classList.remove('ml-64');
      }
    }
  }

  handleSidebar();

  window.addEventListener('resize', handleSidebar);

  hamburger.addEventListener('click', function () {
    const isHidden = sidebar.classList.contains('-translate-x-full');

    mainContent.classList.add('transition-all', 'duration-300', 'ease-in-out');
    
    sidebar.classList.toggle('-translate-x-full');

    if (window.innerWidth >= 1024) {
      if (isHidden) {
        mainContent.classList.add('ml-64');
      } else {
        mainContent.classList.remove('ml-64');
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

document.addEventListener('DOMContentLoaded', function () {
  const ctx = document.getElementById('myChart').getContext('2d');

  const myChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'August'],
      datasets: [{
        data: [100, 150, 60, 140, 90, 200, 130, 160],
        fill: true,
        borderColor: 'rgba(54, 162, 235, 1)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false 
        },
        title: {
          display: true,
          text: 'Active Lecturer'
        }
      },
      scales: {
        x: {
          ticks: {
            display: true
          },
          grid: {
            display: true
          }
        },
        y: {
          ticks: {
            display: true
          },
          grid: {
            display: true 
          }
        }
      }
    }
  })
});