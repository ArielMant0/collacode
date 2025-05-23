<template>
    <div>
        <nav class="topnav d-flex align-stretch justify-center">
            <NavLink to="/coding" text="back to coding" icon="mdi-arrow-left" style="position: absolute; left: 2px;"/>
            <NavLink to="/admin/users" :active="route.path" text="users" icon="mdi-account-multiple"/>
            <NavLink to="/admin/projects" :active="route.path" text="projects" icon="mdi-file-multiple"/>
        </nav>

        <div class="pa-2 d-flex align-center justify-center">
            <div v-if="isAdmin">
                <router-view/>
            </div>
            <div v-else class="text-h2">
                You are not an admin <b>:(</b>
            </div>
        </div>
    </div>
</template>

<script setup>
    import NavLink from '@/components/NavLink.vue';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import { onMounted } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

    const app = useApp()
    const { isAdmin } = storeToRefs(app)
    const route = useRoute()
    const router = useRouter()

    onMounted(function() {
        const pages = route.path.split("/").filter(d => d.length > 0)
        if (pages.length < 2) {
            router.push("/admin/users")
        }
    })
</script>