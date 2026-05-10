import { createRouter, createWebHistory } from 'vue-router';
import ArticleDetailView from '@/views/ArticleDetailView.vue';
import DictionaryView from '@/views/DictionaryView.vue';
import NewsView from '@/views/NewsView.vue';
import StubView from '@/views/StubView.vue';

export const routes = [
  {
    path: '/',
    name: 'home',
    component: NewsView,
    meta: { title: 'News' },
  },
  {
    path: '/articles/:id',
    name: 'article',
    component: ArticleDetailView,
    meta: { title: 'Artikel' },
  },
  {
    path: '/woerterbuch',
    name: 'dictionary',
    component: DictionaryView,
    meta: { title: 'Wörterbuch' },
  },
  {
    path: '/stub',
    name: 'stub',
    component: StubView,
    meta: { title: 'Platzhalter' },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
