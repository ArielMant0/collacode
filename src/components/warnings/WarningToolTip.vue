<template>
    <ToolTip :x="wX" :y="wY" :data="warning" align="right">
        <template v-slot:default>
            <div>
                <div>{{ warning.tag_name }} ({{ warning.count }})</div>
                <div>{{ warning.explanation }}</div>
                <div class="d-flex flex-wrap" style="max-width: 100%;">
                    <ItemTeaser  v-for="id in warning.items"
                        :id="id"
                        :width="80"
                        :height="40"
                        class="mr-1 mb-1"/>
                </div>
            </div>
        </template>
    </ToolTip>
</template>

<script setup>
    import { useTooltip } from '@/store/tooltip';
    import ToolTip from '../ToolTip.vue';
    import { storeToRefs } from 'pinia';
    import ItemTeaser from '../items/ItemTeaser.vue';

    const tt = useTooltip()
    const { warning, wX, wY } = storeToRefs(tt)

</script>