
<template>
    <div class="ma-4">
        <CSVImporter v-if="app.activeUserId > 0"/>
    </div>
</template>

<script setup>
    import CSVImporter from '@/components/CSVImporter.vue';
    import { useApp } from '@/store/app';
    import { loadAllUsers } from '@/use/utility';
    import { onMounted } from 'vue';

    const app = useApp()

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
