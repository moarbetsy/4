class EnhancedCamoufoxDashboard {
    constructor() {
        this.profiles = [];
        this.selectedProfiles = new Set();
        this.apiBaseUrl = '/api';
        this.hostInfo = null;
        this.screenSizes = [];
        this.distributionCounter = 0;
        this.init();
    }

    async init() {
        await this.loadHostInfo();
        await this.loadScreenSizes();
        this.bindEvents();
        this.loadProfiles();
    }

    async loadHostInfo() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/host-info`);
            if (response.ok) {
                this.hostInfo = await response.json();
                this.updateHostOSInfo();
            }
        } catch (error) {
            console.error('Error loading host info:', error);
        }
    }

    async loadScreenSizes() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/screen-sizes`);
            if (response.ok) {
                this.screenSizes = await response.json();
            }
        } catch (error) {
            console.error('Error loading screen sizes:', error);
        }
    }

    updateHostOSInfo() {
        const hostOSInfo = document.getElementById('host-os-info');
        if (this.hostInfo) {
            hostOSInfo.innerHTML = `
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-sm text-[#3fb950]">computer</span>
                    <span>Detected: ${this.hostInfo.os} ${this.hostInfo.version || ''}</span>
                </div>
            `;
        }
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

        // Screen mode change
        document.getElementById('screen-mode').addEventListener('change', (e) => {
            this.handleScreenModeChange(e.target.value);
        });

        // Use host OS checkbox
        document.getElementById('use-host-os').addEventListener('change', (e) => {
            this.handleUseHostOSChange(e.target.checked);
        });

        // Proxy URL validation
        document.getElementById('proxy-url').addEventListener('blur', (e) => {
            this.validateProxyURL(e.target.value);
        });
        
        // Real-time proxy validation
        document.getElementById('proxy-url').addEventListener('input', (e) => {
            // Debounce the validation to avoid too many API calls
            clearTimeout(this.proxyValidationTimeout);
            this.proxyValidationTimeout = setTimeout(() => {
                this.validateProxyURL(e.target.value);
            }, 500);
        });

        // Add distribution button
        document.getElementById('add-distribution-btn').addEventListener('click', () => {
            this.addDistributionItem();
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

    handleScreenModeChange(mode) {
        const fixedConfig = document.getElementById('fixed-screen-config');
        const customConfig = document.getElementById('custom-distribution-config');
        
        // Hide all configs first
        fixedConfig.classList.add('hidden');
        customConfig.classList.add('hidden');
        
        // Show relevant config
        if (mode === 'fixed_profile') {
            fixedConfig.classList.remove('hidden');
        } else if (mode === 'custom_distribution') {
            customConfig.classList.remove('hidden');
            // Add initial distribution item if none exist
            if (document.getElementById('distribution-list').children.length === 0) {
                this.addDistributionItem();
            }
        }
    }

    handleUseHostOSChange(useHostOS) {
        const osOverrideSection = document.getElementById('os-override-section');
        if (useHostOS) {
            osOverrideSection.classList.add('hidden');
        } else {
            osOverrideSection.classList.remove('hidden');
        }
    }

    async validateProxyURL(proxyURL) {
        const validationResult = document.getElementById('proxy-validation-result');
        
        if (!proxyURL.trim()) {
            validationResult.classList.add('hidden');
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/validate-proxy`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ proxy: proxyURL })
            });

            const result = await response.json();
            
            validationResult.classList.remove('hidden');
            if (result.valid) {
                validationResult.innerHTML = `
                    <div class="flex items-center gap-2 text-[#3fb950] text-xs">
                        <span class="material-symbols-outlined text-sm">check_circle</span>
                        <span>Valid proxy format: ${result.sanitized_url}</span>
                    </div>
                `;
                if (result.warnings && result.warnings.length > 0) {
                    validationResult.innerHTML += `
                        <div class="flex items-center gap-2 text-[#f79009] text-xs mt-1">
                            <span class="material-symbols-outlined text-sm">warning</span>
                            <span>${result.warnings.join(', ')}</span>
                        </div>
                    `;
                }
            } else {
                validationResult.innerHTML = `
                    <div class="flex items-center gap-2 text-[#f85149] text-xs">
                        <span class="material-symbols-outlined text-sm">error</span>
                        <span>Invalid proxy format: ${result.errors ? result.errors.join(', ') : 'Unknown error'}</span>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error validating proxy:', error);
        }
    }

    addDistributionItem() {
        const distributionList = document.getElementById('distribution-list');
        const itemId = `distribution-item-${this.distributionCounter++}`;
        
        const itemHTML = `
            <div id="${itemId}" class="flex items-center gap-3 p-3 border border-[#30363d] rounded-md">
                <div class="flex-1 grid grid-cols-3 gap-2">
                    <input type="number" placeholder="Width" class="distribution-width w-full rounded-md border border-[#30363d] bg-[#0d1117] py-1 px-2 text-sm text-[#c9d1d9] placeholder:text-[#6e7681]">
                    <input type="number" placeholder="Height" class="distribution-height w-full rounded-md border border-[#30363d] bg-[#0d1117] py-1 px-2 text-sm text-[#c9d1d9] placeholder:text-[#6e7681]">
                    <input type="number" placeholder="Weight %" class="distribution-weight w-full rounded-md border border-[#30363d] bg-[#0d1117] py-1 px-2 text-sm text-[#c9d1d9] placeholder:text-[#6e7681]">
                </div>
                <button type="button" class="text-[#f85149] hover:text-[#ff7b72]" onclick="this.parentElement.remove()">
                    <span class="material-symbols-outlined text-sm">delete</span>
                </button>
            </div>
        `;
        
        distributionList.insertAdjacentHTML('beforeend', itemHTML);
    }

    async loadProfiles() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/profiles`);
            if (response.ok) {
                this.profiles = await response.json();
                this.renderProfiles();
            } else {
                console.error('Failed to load profiles');
                this.loadSampleData();
            }
        } catch (error) {
            console.error('Error loading profiles:', error);
            this.loadSampleData();
        }
    }

    loadSampleData() {
        this.profiles = [
            {
                id: '1',
                name: 'Zenith Explorer',
                screen_mode: 'random_session',
                proxy_url: null,
                effective_os: 'windows',
                status: 'active',
                created_at: new Date().toISOString()
            },
            {
                id: '2',
                name: 'Stealth Navigator',
                screen_mode: 'fixed_profile',
                proxy_url: 'http://proxy.example.com:8080',
                effective_os: 'macos',
                status: 'inactive',
                created_at: new Date().toISOString()
            },
            {
                id: '3',
                name: 'Ghost Protocol',
                screen_mode: 'custom_distribution',
                proxy_url: null,
                effective_os: 'linux',
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
                <td class="table-cell whitespace-nowrap text-sm gh-text-muted">
                    <span class="inline-flex items-center gap-1">
                        <span class="material-symbols-outlined text-sm">${this.getScreenModeIcon(profile.screen_mode)}</span>
                        ${this.formatScreenMode(profile.screen_mode)}
                    </span>
                </td>
                <td class="table-cell whitespace-nowrap text-sm gh-text-muted">
                    ${profile.has_proxy ? 
                        `<span class="inline-flex items-center gap-1 text-[#3fb950]">
                            <span class="material-symbols-outlined text-sm">vpn_lock</span>
                            ${profile.proxy_host || 'Enabled'}
                        </span>` : 
                        `<span class="gh-text-muted">None</span>`
                    }
                </td>
                <td class="table-cell whitespace-nowrap text-sm gh-text-muted">
                    <span class="inline-flex items-center gap-1">
                        <span class="material-symbols-outlined text-sm">${this.getOSIcon(profile.effective_os)}</span>
                        ${this.formatOS(profile.effective_os)}
                    </span>
                </td>
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

    getScreenModeIcon(mode) {
        switch (mode) {
            case 'random_session': return 'shuffle';
            case 'fixed_profile': return 'lock';
            case 'custom_distribution': return 'tune';
            default: return 'monitor';
        }
    }

    formatScreenMode(mode) {
        switch (mode) {
            case 'random_session': return 'Random';
            case 'fixed_profile': return 'Fixed';
            case 'custom_distribution': return 'Custom';
            default: return mode;
        }
    }

    getOSIcon(os) {
        switch (os?.toLowerCase()) {
            case 'windows': return 'desktop_windows';
            case 'macos': return 'laptop_mac';
            case 'linux': return 'terminal';
            default: return 'computer';
        }
    }

    formatOS(os) {
        switch (os?.toLowerCase()) {
            case 'windows': return 'Windows';
            case 'macos': return 'macOS';
            case 'linux': return 'Linux';
            default: return os || 'Unknown';
        }
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
            profile.screen_mode.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (profile.effective_os && profile.effective_os.toLowerCase().includes(searchTerm.toLowerCase()))
        );
        this.renderProfiles(filtered);
    }

    showAddProfileModal() {
        document.getElementById('add-profile-modal').classList.remove('hidden');
        document.getElementById('add-profile-modal').classList.add('flex');
        // Reset form state
        this.handleScreenModeChange('random_session');
        this.handleUseHostOSChange(true);
    }

    hideAddProfileModal() {
        document.getElementById('add-profile-modal').classList.add('hidden');
        document.getElementById('add-profile-modal').classList.remove('flex');
        document.getElementById('add-profile-form').reset();
        // Clear dynamic content
        document.getElementById('distribution-list').innerHTML = '';
        document.getElementById('proxy-validation-result').classList.add('hidden');
        this.distributionCounter = 0;
    }

    async handleAddProfile(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        // Build profile data
        const profileData = {
            name: formData.get('name'),
            timezone: formData.get('timezone'),
            screen_mode: formData.get('screen_mode'),
            use_host_os: formData.has('use_host_os'),
            humanize: formData.has('humanize'),
            headless: formData.has('headless')
        };

        // Add proxy URL if provided
        const proxyURL = formData.get('proxy_url');
        if (proxyURL && proxyURL.trim()) {
            profileData.proxy = proxyURL.trim();
        }

        // Add OS override if not using host OS
        if (!profileData.use_host_os) {
            const osOverride = formData.get('os_override');
            if (osOverride) {
                profileData.os_override = osOverride;
            }
        }

        // Add screen configuration based on mode
        if (profileData.screen_mode === 'fixed_profile') {
            const width = formData.get('fixed_screen_width');
            const height = formData.get('fixed_screen_height');
            if (width && height) {
                profileData.fixed_screen = {
                    screen_width: parseInt(width),
                    screen_height: parseInt(height),
                    window_width: parseInt(width) - 100,
                    window_height: parseInt(height) - 100
                };
            }
        } else if (profileData.screen_mode === 'custom_distribution') {
            const distributionItems = document.querySelectorAll('#distribution-list > div');
            const distribution = [];
            
            distributionItems.forEach(item => {
                const width = item.querySelector('.distribution-width').value;
                const height = item.querySelector('.distribution-height').value;
                const weight = item.querySelector('.distribution-weight').value;
                
                if (width && height && weight) {
                    distribution.push({
                        screen_width: parseInt(width),
                        screen_height: parseInt(height),
                        window_width: parseInt(width) - 100,
                        window_height: parseInt(height) - 100,
                        weight: parseFloat(weight)
                    });
                }
            });
            
            if (distribution.length > 0) {
                profileData.distribution = distribution;
            }
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/profiles/enhanced`, {
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
                this.showNotification('Enhanced profile created successfully', 'success');
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create profile');
            }
        } catch (error) {
            console.error('Error creating profile:', error);
            this.showNotification(`Error creating profile: ${error.message}`, 'error');
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
                const error = await response.json();
                throw new Error(error.detail || 'Failed to launch profile');
            }
        } catch (error) {
            console.error('Error launching profile:', error);
            this.showNotification(`Error launching profile: ${error.message}`, 'error');
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
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete profile');
            }
        } catch (error) {
            console.error('Error deleting profile:', error);
            this.showNotification(`Error deleting profile: ${error.message}`, 'error');
        }
    }

    async deleteSelectedProfiles() {
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

        // Remove notification after 5 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }
}

// Initialize the enhanced dashboard when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new EnhancedCamoufoxDashboard();
});