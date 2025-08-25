<template>
    <div class="pa-2 d-flex align-center justify-center">
        <div v-if="isAdmin">
            <router-view/>
        </div>
        <div v-else class="text-h2 mt-12">
            You are not an admin <b>:(</b>
        </div>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';

    const app = useApp()
    const { isAdmin } = storeToRefs(app)

</script>