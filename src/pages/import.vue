
<template>
    <div class="ma-4">
        <CSVImporter v-if="!isLoading && app.activeUserId > 0"/>
    </div>
</template>

<script setup>
    import CSVImporter from '@/components/CSVImporter.vue';
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { loadAllUsers } from '@/use/utility';
    import { storeToRefs } from 'pinia';
    import { onMounted } from 'vue';

    const app = useApp()
    const settings = useSettings()
    const { isLoading } = storeToRefs(settings)

    async function loadUsers() {
        try {
            const list = await loadAllUsers()
            app.setGlobalUsers(list)
        } catch {
            console.error("could not load users")
            setTimeout(loadUsers, 200)
        }
    }

    onMounted(loadUsers)
</script>
