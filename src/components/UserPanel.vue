<template>
    <v-list v-if="app.users">
        <v-list-item v-for="user in app.users"
            :key="user.id"
            :title="user.name"
            :subtitle="user.id + ' - ' + user.role"
            density="compact"
            hide-details
            @click="selectUser(user.id)">

            <template v-slot:prepend>
                <v-card size="small"
                    density="comfortable"
                    elevation="0"
                    rounded="circle"
                    class="pa-1 mr-4 d-flex"
                    :color="getUseColor(user.id, user.color)">
                    <v-icon color="white">mdi-account</v-icon>
                </v-card>
            </template>
        </v-list-item>
    </v-list>
</template>

<script setup>
    import { useApp } from '@/store/app'

    const app = useApp()

    function getUseColor(id, color) {
        return app.activeUserId !== null ?
            (app.activeUserId === id ? color : color + "66") :
            color
    }

    function selectUser(id) {
        app.setActiveUser(id)
    }

</script>