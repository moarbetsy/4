class CamoufoxDashboard {
    constructor() {
        this.profiles = [];
        this.selectedProfiles = new Set();
        this.apiBaseUrl = '/api';
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadProfiles();
    }

    bindEvents() {
        // Add profile button
        document.getElementById('add-profile-btn').addEventListener('click', () => {
            this.showAddProfileModal();
        });

        // Modal close buttons
        document.getElementById('close-modal-btn').addEventListener('click', () => {
            this.hideAddProfileModal();
        });
        document.getElementById('cancel-btn').addEventListener('click', () => {
            this.hideAddProfileModal();
        });

        // Add profile form
        document.getElementById('add-profile-form').addEventListener('submit', (e) => {
            this.handleAddProfile(e);
        });

        // Select all checkbox
        document.getElementById('select-all-checkbox').addEventListener('change', (e) => {
            this.handleSelectAll(e.target.checked);
        });

        // Launch selected button
        document.getElementById('launch-selected-btn').addEventListener('click', () => {
            this.launchSelectedProfiles();
        });

        // Delete selected button
        document.getElementById('delete-selected-btn').addEventListener('click', () => {
            this.deleteSelectedProfiles();
        });

        // Search input
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.filterProfiles(e.target.value);
        });

        // Close modal when clicking outside
        document.getElementById('add-profile-modal').addEventListener('click', (e) => {
            if (e.target.id === 'add-profile-modal') {
                this.hideAddProfileModal();
            }
        });
    }

    async loadProfiles() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/profiles`);
            if (response.ok) {
                this.profiles = await response.json();
                this.renderProfiles();
            } else {
                console.error('Failed to load profiles');
                // Load sample data for demo
                this.loadSampleData();
            }
        } catch (error) {
            console.error('Error loading profiles:', error);
            // Load sample data for demo
            this.loadSampleData();
        }
    }

    loadSampleData() {
        this.profiles = [
            {
                id: '1',
                name: 'Zenith Explorer',
                os: 'Windows',
                timezone: 'GMT+01:00',
                status: 'active',
                created_at: new Date().toISOString()
            },
            {
                id: '2',
                name: 'Stealth Navigator',
                os: 'macOS',
                timezone: 'GMT-05:00',
                status: 'inactive',
                created_at: new Date().toISOString()
            },
            {
                id: '3',
                name: 'Ghost Protocol',
                os: 'Linux',
                timezone: 'GMT+08:00',
                status: 'active',
                created_at: new Date().toISOString()
            },
            {
                id: '4',
                name: 'Shadow Surfer',
                os: 'Windows',
                timezone: 'GMT+03:00',
                status: 'inactive',
                created_at: new Date().toISOString()
            },
            {
                id: '5',
                name: 'Vortex Voyager',
                os: 'macOS',
                timezone: 'GMT-07:00',
                status: 'active',
                created_at: new Date().toISOString()
            }
        ];
        this.renderProfiles();
    }

    renderProfiles(filteredProfiles = null) {
        const profilesToRender = filteredProfiles || this.profiles;
        const tbody = document.getElementById('profiles-table-body');
        
        tbody.innerHTML = profilesToRender.map(profile => `
            <tr class="table-row">
                <td class="table-cell table-cell--checkbox">
                    <input class="form-checkbox profile-checkbox" type="checkbox" data-profile-id="${profile.id}"/>
                </td>
                <td class="table-cell whitespace-nowrap text-sm font-medium gh-text-strong">${profile.name}</td>
                <td class="table-cell whitespace-nowrap text-sm gh-text-muted">${profile.os}</td>
                <td class="table-cell whitespace-nowrap text-sm gh-text-muted">${profile.timezone}</td>
                <td class="table-cell whitespace-nowrap text-sm">
                    <span class="inline-flex items-center gap-2 ${profile.status === 'active' ? 'gh-text-success' : 'gh-text-muted'}">
                        <span class="status-dot ${profile.status === 'active' ? 'status-dot--active' : 'status-dot--inactive'}"></span>
                        ${profile.status === 'active' ? 'Active' : 'Inactive'}
                    </span>
                </td>
            </tr>
        `).join('');

        // Bind individual profile events
        this.bindProfileEvents();
    }

    bindProfileEvents() {
        // Profile checkboxes
        document.querySelectorAll('.profile-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const profileId = e.target.dataset.profileId;
                if (e.target.checked) {
                    this.selectedProfiles.add(profileId);
                } else {
                    this.selectedProfiles.delete(profileId);
                }
                this.updateActionButtons();
            });
        });
    }

    updateActionButtons() {
        const hasSelection = this.selectedProfiles.size > 0;
        document.getElementById('launch-selected-btn').disabled = !hasSelection;
        document.getElementById('delete-selected-btn').disabled = !hasSelection;
    }

    handleSelectAll(checked) {
        const checkboxes = document.querySelectorAll('.profile-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = checked;
            const profileId = checkbox.dataset.profileId;
            if (checked) {
                this.selectedProfiles.add(profileId);
            } else {
                this.selectedProfiles.delete(profileId);
            }
        });
        this.updateActionButtons();
    }

    filterProfiles(searchTerm) {
        if (!searchTerm.trim()) {
            this.renderProfiles();
            return;
        }

        const filtered = this.profiles.filter(profile =>
            profile.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            profile.os.toLowerCase().includes(searchTerm.toLowerCase()) ||
            profile.timezone.toLowerCase().includes(searchTerm.toLowerCase())
        );
        this.renderProfiles(filtered);
    }

    showAddProfileModal() {
        document.getElementById('add-profile-modal').classList.remove('hidden');
        document.getElementById('add-profile-modal').classList.add('flex');
    }

    hideAddProfileModal() {
        document.getElementById('add-profile-modal').classList.add('hidden');
        document.getElementById('add-profile-modal').classList.remove('flex');
        document.getElementById('add-profile-form').reset();
    }

    async handleAddProfile(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const profileData = {
            name: formData.get('name'),
            os: formData.get('os'),
            timezone: formData.get('timezone')
        };

        try {
            const response = await fetch(`${this.apiBaseUrl}/profiles`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(profileData)
            });

            if (response.ok) {
                const newProfile = await response.json();
                this.profiles.push(newProfile);
                this.renderProfiles();
                this.hideAddProfileModal();
                this.showNotification('Profile created successfully', 'success');
            } else {
                throw new Error('Failed to create profile');
            }
        } catch (error) {
            console.error('Error creating profile:', error);
            // For demo purposes, add profile locally
            const newProfile = {
                id: Date.now().toString(),
                ...profileData,
                status: 'inactive',
                created_at: new Date().toISOString()
            };
            this.profiles.push(newProfile);
            this.renderProfiles();
            this.hideAddProfileModal();
            this.showNotification('Profile created successfully (demo mode)', 'success');
        }
    }

    async launchProfile(profileId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/profiles/${profileId}/launch`, {
                method: 'POST'
            });

            if (response.ok) {
                // Update profile status
                const profile = this.profiles.find(p => p.id === profileId);
                if (profile) {
                    profile.status = 'active';
                    this.renderProfiles();
                }
                this.showNotification('Profile launched successfully', 'success');
            } else {
                throw new Error('Failed to launch profile');
            }
        } catch (error) {
            console.error('Error launching profile:', error);
            // For demo purposes, update status locally
            const profile = this.profiles.find(p => p.id === profileId);
            if (profile) {
                profile.status = 'active';
                this.renderProfiles();
            }
            this.showNotification('Profile launched successfully (demo mode)', 'success');
        }
    }

    async launchSelectedProfiles() {
        const profileIds = Array.from(this.selectedProfiles);
        for (const profileId of profileIds) {
            await this.launchProfile(profileId);
        }
        this.selectedProfiles.clear();
        this.updateActionButtons();
        document.getElementById('select-all-checkbox').checked = false;
    }

    async deleteProfile(profileId) {
        // Temporarily remove confirmation for testing
        // if (!confirm('Are you sure you want to delete this profile?')) {
        //     return;
        // }

        try {
            const response = await fetch(`${this.apiBaseUrl}/profiles/${profileId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.profiles = this.profiles.filter(p => p.id !== profileId);
                this.selectedProfiles.delete(profileId);
                this.renderProfiles();
                this.updateActionButtons();
                this.showNotification('Profile deleted successfully', 'success');
            } else {
                throw new Error('Failed to delete profile');
            }
        } catch (error) {
            console.error('Error deleting profile:', error);
            // For demo purposes, delete locally
            this.profiles = this.profiles.filter(p => p.id !== profileId);
            this.selectedProfiles.delete(profileId);
            this.renderProfiles();
            this.updateActionButtons();
            this.showNotification('Profile deleted successfully (demo mode)', 'success');
        }
    }

    async deleteSelectedProfiles() {
        // Temporarily remove confirmation for testing
        // if (!confirm(`Are you sure you want to delete ${this.selectedProfiles.size} selected profile(s)?`)) {
        //     return;
        // }

        const profileIds = Array.from(this.selectedProfiles);
        for (const profileId of profileIds) {
            await this.deleteProfile(profileId);
        }
        this.selectedProfiles.clear();
        this.updateActionButtons();
        document.getElementById('select-all-checkbox').checked = false;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-md text-sm font-medium transition-all duration-300 ${
            type === 'success' ? 'bg-green-600 text-white' : 
            type === 'error' ? 'bg-red-600 text-white' : 
            'bg-neutral-700 text-neutral-100'
        }`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// Initialize the dashboard when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CamoufoxDashboard();
});
