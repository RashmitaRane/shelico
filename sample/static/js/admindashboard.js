document.addEventListener("DOMContentLoaded", function() {
    // DOM Elements
    const toggleSidebar = document.querySelector('.toggle-sidebar');
    const sidebar = document.getElementById('sidebar');
    const navbar = document.querySelector('nav');
    const searchInput = document.querySelector('.search-container input');
    const searchIcon = document.querySelector('.search-container i');
    const dynamicActionBtn = document.getElementById('dynamicActionBtn');
    const dynamicActionBtnText = dynamicActionBtn.querySelector('span');
    
    // Popup elements
    const helplineFormPopup = document.getElementById('helplineFormPopup');
    const mythFormPopup = document.getElementById('mythFormPopup');
    const closePopupBtns = document.querySelectorAll('.close-popup');
    
    const profileIcon = document.getElementById('profileIcon');
    const dropdown = document.getElementById('dropdownContent');

    // Track active confirmation dialog
    let activeConfirmationDialog = null;

    // Initialize UI
    initUI();
    
    // Content configuration
    const contentConfig = {
        'query-content': {
            searchPlaceholder: 'Search a query...',
            actionButtonText: '',
            showActionButton: false,
            searchAction: searchQueries
        },
        'helpline-content': {
            searchPlaceholder: 'Search health helplines...',
            actionButtonText: 'Post Helpline',
            showActionButton: true,
            searchAction: searchHelplines,
            popup: helplineFormPopup,
            loadData: loadHelplines
        },
        'myth-content': {
            searchPlaceholder: 'Search a myth...',
            actionButtonText: 'Post Myth',
            showActionButton: true,
            searchAction: searchMyths,
            popup: mythFormPopup,
            loadData: loadMythCards
        },
        'storyboard-content': {
            searchPlaceholder: 'Search stories...',
            actionButtonText: '',
            showActionButton: false,
            searchAction: searchStories
        }
    };

    // Initialize with default content
    updateUIForContent('query-content');
    loadInitialData();

    // Event Listeners
    setupEventListeners();

    // Helper Functions
    function initUI() {
        // Fix layout shift on fresh load
        if (sidebar && navbar) {
            if (!sidebar.classList.contains('hide')) {
                navbar.style.width = "calc(100% - 260px)";
                navbar.style.left = "260px";
            }
        }
    }

    function setupEventListeners() {
        // Profile dropdown functionality
        if (profileIcon && dropdown) {
            profileIcon.addEventListener('click', function(event) {
                event.stopPropagation();
                dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
            });

            // Close dropdown if clicked outside
            document.addEventListener('click', function(event) {
                if (!dropdown.contains(event.target) && event.target !== profileIcon) {
                    dropdown.style.display = 'none';
                }
            });
        }

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
                
                // Load data for the active content if it has a loadData function
                if (contentConfig[targetId]?.loadData) {
                    contentConfig[targetId].loadData();
                }
            });
        });

        // Search functionality
        if (searchIcon && searchInput) {
            searchIcon.addEventListener('click', handleSearch);
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') handleSearch();
            });
        }

        // Dynamic action button click handler
        dynamicActionBtn.addEventListener('click', handleActionButtonClick);

        // Close popup handlers
        closePopupBtns.forEach(btn => {
            btn.addEventListener('click', () => closePopup(btn.closest('.popup-overlay')));
        });

        // Close popup when clicking outside
        document.querySelectorAll('.popup-overlay').forEach(popup => {
            popup.addEventListener('click', function(e) {
                if (e.target === this) {
                    closePopup(this);
                }
            });
        });

        // Form submissions
        setupFormHandlers();

        // Handle dropdown menus
        document.addEventListener('click', function(e) {
            // Toggle dropdown menus
            const actionBtn = e.target.closest('.item-actions');
            if (actionBtn) {
                e.stopPropagation();
                const dropdownMenu = actionBtn.nextElementSibling;
                dropdownMenu.style.display = dropdownMenu.style.display === 'block' ? 'none' : 'block';
                
                // Close other dropdowns
                document.querySelectorAll('.dropdown-menu').forEach(menu => {
                    if (menu !== dropdownMenu) {
                        menu.style.display = 'none';
                    }
                });
            }
            
            // Close all dropdowns when clicking outside
            if (!e.target.closest('.dropdown-menu') && !e.target.closest('.item-actions')) {
                document.querySelectorAll('.dropdown-menu').forEach(menu => {
                    menu.style.display = 'none';
                });
            }
        });
    }

    function handleSearch() {
        const activeContent = document.querySelector('.content-section.active').id;
        const query = searchInput.value.trim();
        if (query) {
            contentConfig[activeContent].searchAction(query);
        }
    }

    function handleActionButtonClick() {
        const activeContent = document.querySelector('.content-section.active').id;
        const popup = contentConfig[activeContent].popup;
        if (popup) {
            popup.style.display = 'flex';
            // Reset form mode when adding new
            if (activeContent === 'helpline-content') {
                const form = document.getElementById('helplineForm');
                delete form.dataset.editId;
                form.querySelector('.submit-btn').textContent = 'Post Helpline';
            } else if (activeContent === 'myth-content') {
                const form = document.getElementById('mythForm');
                delete form.dataset.editId;
                form.querySelector('.submit-btn').textContent = 'Post Myth';
            }
        }
    }

    function closePopup(popup) {
        popup.style.display = 'none';
        // Reset myth form if it's open
        if (popup === mythFormPopup) {
            document.querySelector('.flip-container').classList.remove('flipped');
            document.getElementById('mythForm').reset();
            document.getElementById('factForm').reset();
        }
    }

    function setupFormHandlers() {
        // Helpline Form Submission
        document.getElementById('helplineForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('.submit-btn');
            submitBtn.disabled = true;
            submitBtn.textContent = this.dataset.editId ? 'Updating...' : 'Posting...';
        
            try {
                const title = document.getElementById('helplineTitle').value.trim();
                const description = document.getElementById('helplineDescription').value.trim();
                
                if (!title || !description) {
                    throw new Error('Please fill in all fields');
                }
                
                const url = this.dataset.editId ? '/update_helpline' : '/add_helpline';
                const body = this.dataset.editId ? 
                    { h_id: this.dataset.editId, title, description } : 
                    { title, description };
                
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(body)
                });
        
                const data = await response.json();
        
                if (!response.ok || data.status !== 'success') {
                    throw new Error(data.message || 'Failed to process helpline');
                }
        
                // Success case
                loadHelplines();
                this.reset();
                delete this.dataset.editId;
                submitBtn.textContent = 'Post Helpline';
                helplineFormPopup.style.display = 'none';
                showSuccessMessage(data.message || (this.dataset.editId ? 'Helpline updated!' : 'Helpline added successfully!'));
            } catch (error) {
                console.error('Error:', error);
                showErrorMessage(error.message || 'An error occurred');
            } finally {
                submitBtn.disabled = false;
            }
        });
        
        // Myth form handling
        let currentMyth = null;
        
        document.getElementById('mythForm').addEventListener('submit', function(e) {
            e.preventDefault();
            currentMyth = document.getElementById('mythText').value.trim();
            if (!currentMyth) {
                showErrorMessage('Please enter a myth');
                return;
            }
            document.querySelector('.flip-container').classList.add('flipped');
        });
        
        document.querySelector('.back-btn').addEventListener('click', function() {
            document.querySelector('.flip-container').classList.remove('flipped');
        });
        
        document.getElementById('factForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('.submit-btn');
            submitBtn.disabled = true;
            submitBtn.textContent = this.dataset.editId ? 'Updating...' : 'Posting...';

            try {
                const fact = document.getElementById('factText').value.trim();
                
                if (!fact || !currentMyth) {
                    throw new Error('Please fill in all fields');
                }
                
                const url = this.dataset.editId ? '/update_myth_card' : '/add_myth_card';
                const body = this.dataset.editId ? 
                    { myth_id: this.dataset.editId, myth: currentMyth, fact } : 
                    { myth: currentMyth, fact };
                
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(body)
                });

                const data = await response.json();

                if (!response.ok || data.status !== 'success') {
                    throw new Error(data.message || 'Failed to process myth card');
                }

                // Success case
                loadMythCards();
                document.getElementById('mythForm').reset();
                this.reset();
                delete this.dataset.editId;
                submitBtn.textContent = 'Post Myth Card';
                mythFormPopup.style.display = 'none';
                document.querySelector('.flip-container').classList.remove('flipped');
                showSuccessMessage(data.message || (this.dataset.editId ? 'Myth card updated!' : 'Myth card added successfully!'));
            } catch (error) {
                console.error('Error:', error);
                showErrorMessage(error.message || 'An error occurred');
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    function updateUIForContent(contentId) {
        const config = contentConfig[contentId];
        
        // Update search placeholder
        if (searchInput) {
            searchInput.placeholder = config.searchPlaceholder;
            searchInput.value = '';
        }
        
        // Update action button
        if (dynamicActionBtn) {
            dynamicActionBtn.style.display = config.showActionButton ? 'flex' : 'none';
            dynamicActionBtnText.textContent = config.actionButtonText;
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
        // Implement actual search functionality here
    }

    function searchHelplines(query) {
        console.log(`Searching health helplines for: ${query}`);
        // Implement actual search functionality here
    }

    function searchMyths(query) {
        console.log(`Searching myths for: ${query}`);
        // Implement actual search functionality here
    }

    function searchStories(query) {
        console.log(`Searching stories for: ${query}`);
        // Implement actual search functionality here
    }

    // Load initial data from database
    function loadInitialData() {
        loadHelplines();
        loadMythCards();
    }
    
    function loadHelplines() {
        fetch('/get_helplines')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const helplineList = document.getElementById('helplineList');
                helplineList.innerHTML = '';
                
                if (data.status === 'success' && data.helplines && data.helplines.length > 0) {
                    data.helplines.forEach(helpline => {
                        const item = document.createElement('div');
                        item.className = 'query-item';
                        item.innerHTML = `
                            <div class="item-header">
                                <h3>${helpline.title || 'Untitled'}</h3>
                                <div class="dropdown">
                                    <button class="item-actions">⋯</button>
                                    <div class="dropdown-menu">
                                        <button class="edit-btn helpline-edit-btn" data-id="${helpline.h_id}">Edit</button>
                                        <button class="delete-btn helpline-delete-btn" data-id="${helpline.h_id}">Delete</button>
                                    </div>
                                </div>
                            </div>
                            <p>${helpline.description || 'No description provided'}</p>
                        `;
                        helplineList.appendChild(item);
                    });

                    // Event delegation for edit/delete buttons
                    helplineList.addEventListener('click', function(e) {
                        const editBtn = e.target.closest('.helpline-edit-btn');
                        const deleteBtn = e.target.closest('.helpline-delete-btn');
                        
                        if (editBtn) {
                            handleEditHelpline(editBtn.dataset.id);
                        }
                        
                        if (deleteBtn) {
                            handleDeleteHelpline(deleteBtn.dataset.id);
                        }
                    });
                } else {
                    helplineList.innerHTML = '<p class="no-data">No helplines available</p>';
                }
            })
            .catch(error => {
                console.error("Error loading helplines:", error);
                const helplineList = document.getElementById('helplineList');
                helplineList.innerHTML = '<p class="error-message">Failed to load helplines. Please try again later.</p>';
            });
    }

    async function handleEditHelpline(h_id) {
        try {
            const response = await fetch(`/get_helpline?id=${h_id}`);
            const data = await response.json();
            
            if (!response.ok || data.status !== 'success') {
                throw new Error(data.message || 'Failed to fetch helpline');
            }
            
            document.getElementById('helplineTitle').value = data.helpline.title;
            document.getElementById('helplineDescription').value = data.helpline.description;
            
            const form = document.getElementById('helplineForm');
            form.dataset.editId = h_id;
            form.querySelector('.submit-btn').textContent = 'Update Helpline';
            
            helplineFormPopup.style.display = 'flex';
        } catch (error) {
            console.error('Error:', error);
            showErrorMessage('Failed to load helpline for editing');
        }
    }

    async function handleDeleteHelpline(h_id) {
        showConfirmationDialog('Are you sure you want to delete this helpline?', async (confirmed) => {
            if (confirmed) {
                try {
                    const response = await fetch('/delete_helpline', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ h_id })
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        loadHelplines();
                        showSuccessMessage('Helpline deleted successfully');
                    } else {
                        throw new Error(data.message || 'Failed to delete helpline');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    showErrorMessage(error.message || 'Failed to delete helpline');
                }
            }
        });
    }
    
    function loadMythCards() {
        fetch('/get_myth_cards')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const mythCardList = document.getElementById('mythCardList');
                mythCardList.innerHTML = '';
                
                if (data.status === 'success' && data.myth_cards && data.myth_cards.length > 0) {
                    data.myth_cards.forEach(card => {
                        const mythItem = document.createElement('div');
                        mythItem.className = 'myth-card';
                        mythItem.innerHTML = `
                            <div class="item-header">
                                <h3>Myth Card</h3>
                                <div class="dropdown">
                                    <button class="item-actions">⋯</button>
                                    <div class="dropdown-menu">
                                        <button class="edit-btn myth-edit-btn" data-id="${card.myth_id}">Edit</button>
                                        <button class="delete-btn myth-delete-btn" data-id="${card.myth_id}">Delete</button>
                                    </div>
                                </div>
                            </div>
                            <div class="myth-card-content">
                                <p><strong>Myth:</strong> ${card.myth}</p>
                                <p><strong>Fact:</strong> ${card.fact}</p>
                            </div>
                        `;
                        mythCardList.appendChild(mythItem);
                    });

                    // Event delegation for edit/delete buttons
                    mythCardList.addEventListener('click', function(e) {
                        const editBtn = e.target.closest('.myth-edit-btn');
                        const deleteBtn = e.target.closest('.myth-delete-btn');
                        
                        if (editBtn) {
                            handleEditMythCard(editBtn.dataset.id);
                        }
                        
                        if (deleteBtn) {
                            handleDeleteMythCard(deleteBtn.dataset.id);
                        }
                    });
                } else {
                    mythCardList.innerHTML = '<p class="no-data">No myth cards found</p>';
                }
            })
            .catch(error => {
                console.error("Error loading myth cards:", error);
                const mythCardList = document.getElementById('mythCardList');
                mythCardList.innerHTML = '<p class="error-message">Failed to load myth cards. Please try again later.</p>';
            });
    }

    async function handleEditMythCard(myth_id) {
        try {
            const response = await fetch(`/get_myth_card?id=${myth_id}`);
            const data = await response.json();
            
            if (!response.ok || data.status !== 'success') {
                throw new Error(data.message || 'Failed to fetch myth card');
            }
            
            document.getElementById('mythText').value = data.myth_card.myth;
            document.getElementById('factText').value = data.myth_card.fact;
            
            const form = document.getElementById('mythForm');
            form.dataset.editId = myth_id;
            form.querySelector('.submit-btn').textContent = 'Update Myth';
            
            mythFormPopup.style.display = 'flex';
            document.querySelector('.flip-container').classList.add('flipped');
        } catch (error) {
            console.error('Error:', error);
            showErrorMessage('Failed to load myth card for editing');
        }
    }

    async function handleDeleteMythCard(myth_id) {
        showConfirmationDialog('Are you sure you want to delete this myth card?', async (confirmed) => {
            if (confirmed) {
                try {
                    const response = await fetch('/delete_myth_card', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ myth_id })
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        loadMythCards();
                        showSuccessMessage('Myth card deleted successfully');
                    } else {
                        throw new Error(data.message || 'Failed to delete myth card');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    showErrorMessage(error.message || 'Failed to delete myth card');
                }
            }
        });
    }
    
    // Confirmation dialog function
    function showConfirmationDialog(message, callback) {
        // Remove any existing dialog
        if (activeConfirmationDialog) {
            activeConfirmationDialog.remove();
        }
        
        const dialog = document.createElement('div');
        dialog.className = 'confirmation-dialog';
        dialog.innerHTML = `
            <div class="dialog-content">
                <p>${message}</p>
                <div class="dialog-buttons">
                    <button class="confirm-btn">Yes</button>
                    <button class="cancel-btn">Back</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
        activeConfirmationDialog = dialog;
        
        dialog.querySelector('.confirm-btn').addEventListener('click', () => {
            callback(true);
            dialog.remove();
            activeConfirmationDialog = null;
        });
        
        dialog.querySelector('.cancel-btn').addEventListener('click', () => {
            callback(false);
            dialog.remove();
            activeConfirmationDialog = null;
        });
    }

    // Toast message functions
    function showSuccessMessage(message) {
        showToast(message, 'success');
    }

    function showErrorMessage(message) {
        showToast(message, 'error');
    }

    function showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 3000);
    }
});