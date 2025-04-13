document.addEventListener("DOMContentLoaded", function() {
    // DOM Elements
    const toggleSidebar = document.querySelector('.toggle-sidebar');
    const sidebar = document.getElementById('sidebar');
    const navbar = document.querySelector('nav');
    const searchInput = document.querySelector('.search-container input');
    const searchIcon = document.querySelector('.search-container i');
    const notificationBtn = document.querySelector('.notification-btn');
    const askQueryBtn = document.querySelector('.ask-query-btn');
    const askQueryBtnText = askQueryBtn ? askQueryBtn.querySelector('span') : null;

    // Profile dropdown
    const profileIcon = document.getElementById('profileIcon');
    const dropdown = document.getElementById('dropdownContent');

    if (profileIcon && dropdown) {
        profileIcon.addEventListener('click', function (event) {
            event.stopPropagation();
            dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
        });

        // Close dropdown if clicked outside
        document.addEventListener('click', function (event) {
            if (!dropdown.contains(event.target)) {
                dropdown.style.display = 'none';
            }
        });
    }

    // Fix layout shift on fresh load
    window.addEventListener('load', function() {
        if (sidebar && navbar) {
            if (!sidebar.classList.contains('hide')) {
                navbar.style.width = "calc(100% - 260px)";
                navbar.style.left = "260px";
            }
        }
    });

    // Popup Elements
    const queryPopup = document.getElementById("queryPopup");
    const storyPopup = document.getElementById("storyPopup");

    // Initialize popups if they exist
    if (queryPopup || storyPopup) {
        // Query Popup Elements
        const closeQueryPopup = queryPopup ? queryPopup.querySelector(".close-popup") : null;
        const queryText = document.getElementById("queryText");
        const charRemaining = document.getElementById("charRemaining");
        const queryForm = document.getElementById("queryForm");

        // Story Popup Elements
        const closeStoryPopup = storyPopup ? storyPopup.querySelector(".close-popup") : null;
        const storyText = document.getElementById("storyText");
        const storyCharRemaining = document.getElementById("storyCharRemaining");
        const storyForm = document.getElementById("storyForm");

        // Show query popup when Ask Query is clicked
        if (askQueryBtn && queryPopup) {
            askQueryBtn.addEventListener("click", function(e) {
                e.preventDefault();
                const activeSection = document.querySelector(".content-section.active").id;
                
                if (activeSection === "story-content" && storyPopup) {
                    storyPopup.style.display = "flex";
                } else if (queryPopup) {
                    queryPopup.style.display = "flex";
                }
            });
        }

        // Close popups when X is clicked
        if (closeQueryPopup) {
            closeQueryPopup.addEventListener("click", function() {
                queryPopup.style.display = "none";
            });
        }
        
        if (closeStoryPopup) {
            closeStoryPopup.addEventListener("click", function() {
                storyPopup.style.display = "none";
            });
        }

        // Close popups when clicking outside
        window.addEventListener("click", function(e) {
            if (queryPopup && e.target === queryPopup) {
                queryPopup.style.display = "none";
            }
            if (storyPopup && e.target === storyPopup) {
                storyPopup.style.display = "none";
            }
        });

        // Character count for query textarea
        if (queryText && charRemaining) {
            queryText.addEventListener("input", function() {
                charRemaining.textContent = 1000 - queryText.value.length;
            });
        }

        // Character count for story textarea
        if (storyText && storyCharRemaining) {
            storyText.addEventListener("input", function() {
                storyCharRemaining.textContent = 2000 - storyText.value.length;
            });
        }

        // Form submissions
        if (queryForm) {
            queryForm.addEventListener("submit", function(e) {
                e.preventDefault();
                console.log("Query submitted:", {
                    text: queryText.value,
                    visibility: document.querySelector('input[name="visibility"]:checked').value
                });
                queryPopup.style.display = "none";
            });
        }

        if (storyForm) {
            storyForm.addEventListener("submit", function(e) {
                e.preventDefault();
                console.log("Story submitted:", {
                    title: document.getElementById("storyTitle").value,
                    text: storyText.value,
                    visibility: document.querySelector('input[name="storyVisibility"]:checked').value
                });
                storyPopup.style.display = "none";
            });
        }
    }

    // Content configuration
    const contentConfig = {
        'query-content': {
            searchPlaceholder: 'Search a query...',
            showNotification: true,
            showAskButton: true,
            askButtonText: 'Ask Query',
            searchAction: searchQueries
        },
        'helpline-content': {
            searchPlaceholder: 'Search health helplines...',
            showNotification: false,
            showAskButton: false,
            searchAction: searchHelplines
        },
        'myth-content': {
            searchPlaceholder: 'Search a myth...',
            showNotification: false,
            showAskButton: false,
            searchAction: searchMyths
        },
        'story-content': {
            searchPlaceholder: 'Search stories...',
            showNotification: false,
            showAskButton: true,
            askButtonText: 'Post Your Story',
            searchAction: searchStories
        }
    };

    // Initialize with default content (Query Posting)
    updateUIForContent('query-content');

    // Sidebar toggle
    if (toggleSidebar && sidebar) {
        toggleSidebar.addEventListener('click', () => {
            sidebar.classList.toggle('hide');
            navbar.style.width = sidebar.classList.contains('hide') 
                ? "calc(100% - 70px)" 
                : "calc(100% - 260px)";
            navbar.style.left = sidebar.classList.contains('hide') ? "70px" : "260px";
        });
    }

    // Content switching
    const menuItems = document.querySelectorAll('.side-menu li[data-target]');
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('data-target');
            updateUIForContent(targetId);
            setActiveContent(targetId);
        });
    });

    // Search functionality
    if (searchIcon && searchInput) {
        searchIcon.addEventListener('click', () => {
            const activeContent = document.querySelector('.content-section.active').id;
            contentConfig[activeContent].searchAction(searchInput.value);
        });
        
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const activeContent = document.querySelector('.content-section.active').id;
                contentConfig[activeContent].searchAction(searchInput.value);
            }
        });
    }

    // Helper functions
    function updateUIForContent(contentId) {
        const config = contentConfig[contentId];
        
        // Update search placeholder
        if (searchInput) {
            searchInput.placeholder = config.searchPlaceholder;
        }
        
        // Toggle notification button
        if (notificationBtn) {
            notificationBtn.style.display = config.showNotification ? 'block' : 'none';
        }
        
        // Toggle and update ask button
        if (askQueryBtn && askQueryBtnText) {
            askQueryBtn.style.display = config.showAskButton ? 'block' : 'none';
            if (config.showAskButton && config.askButtonText) {
                askQueryBtnText.textContent = config.askButtonText;
            }
        }
    }

    function setActiveContent(targetId) {
        // Remove active class from all menu items and content sections
        document.querySelectorAll('.side-menu li').forEach(i => i.classList.remove('active'));
        document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
        
        // Add active class to clicked menu item and target content
        const menuItem = document.querySelector(`.side-menu li[data-target="${targetId}"]`);
        const contentSection = document.getElementById(targetId);
        
        if (menuItem) menuItem.classList.add('active');
        if (contentSection) contentSection.classList.add('active');
    }

    // Search functions for each content type
    function searchQueries(query) {
        console.log(`Searching queries for: ${query}`);
        // Implement query search logic here
    }

    function searchHelplines(query) {
        console.log(`Searching health helplines for: ${query}`);
        // Implement helpline search logic here
    }

    function searchMyths(query) {
        console.log(`Searching myths for: ${query}`);
        // Implement myth search logic here
    }

    function searchStories(query) {
        console.log(`Searching stories for: ${query}`);
        // Implement story search logic here
    }
});