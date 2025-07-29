document.addEventListener('DOMContentLoaded', function () {
  const path = window.location.pathname;
  
  const navItems = [
   {
      id: 'dashboard-link',
      match: (p) => p.startsWith('/dashboard/'),
    },
    {
      id: 'schedule20251-link',
      match: (p) => p.startsWith('/schedule20251/'), 
    },
    {
      id: 'schedule20252-link',
      match: (p) => p.startsWith('/schedule20252/'), 
    },
    {
      id: 'studyprogram-link',
      match: (p) => p.startsWith('/studyprogram/'), 
    },
    {
      id: 'prediction-link',
      match: (p) => p.startsWith('/prediction/'), 
    },
    {
      id: 'preference-link',
      match: (p) => p.startsWith('/preference/'), 
    },
    {
    id: 'dashboardhsp-link',
    match: (p) => p.startsWith('/dashboard/'),
    },
        {
      id: 'dashboard_lecturer_view-link',
      match: (p) => p.startsWith('/dashboard/lecturerview/'), 
    },
    {
      id: 'viewschedule20251-link',
      match: (p) => p.startsWith('/viewschedule/20251/'), 
    },
    {
      id: 'viewschedule20252-link',
      match: (p) => p.startsWith('/viewschedule/20252/'), 
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
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 250);  
    gradient.addColorStop(0, 'rgba(54, 162, 235, 0.5)');
    gradient.addColorStop(1, 'rgba(54, 162, 235, 0)');

    const myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'August'],
            datasets: [{
                data: [100, 150, 80, 140, 90, 170, 130, 160],
                fill: true,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: gradient,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 8,
                pointHitRadius: 20
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
                    text: 'Active Lecturer',
                    align: 'start',
                    padding: {
                        bottom: 30,
                    },
                    font: {
                        size: 18,
                        weight: 'bold',
                        family: 'poppins'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        display: true
                    },
                    grid: {
                        display: false,
                    }
                },
                y: {
                    min: 60,
                    ticks: {
                        display: false,
                    },
                    grid: {
                        display: true,
                    },
                    border: {
                        dash: [2,4],
                        display: false
                    }
                }
            }
        }
    });

     const container = document.getElementById('myChart').parentElement;

      const observer = new ResizeObserver(() => {
          myChart.resize();
      });
      observer.observe(container);
});



document.getElementById('assignForm').addEventListener('submit', function(event) {
    event.preventDefault(); 

    const form = event.target;
    const formData = new FormData(form);
    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

    const submitBtn = form.querySelector('[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Saving...';
    submitBtn.disabled = true;

    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
        },
        body: formData,
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            Swal.fire({
                position: "top-end",
                icon: "success",
                title: "Assign Lecturer has been saved",
                showConfirmButton: false,
                timer: 1500
            }).then((result) => {
                closeAssign();
                window.location.reload();
            });
        } else {
             Swal.fire({
                position: "top-end",
                icon: "error",
                title: "Oops! Something went wrong",
                showConfirmButton: false,
                timer: 1500
            }).then((result) => {
                closeAssign();
                window.location.reload();
            });
        }
    })
    .catch(error => {
        console.error('Submit error:', error);
        alert('Network error occurred. Please try again.');
    })
    .finally(() => {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    });
});

