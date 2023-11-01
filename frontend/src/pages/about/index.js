import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const About = ({ updateOrders, orders }) => {
  
  return <Main>
    <MetaTags>
      <title>О проекте</title>
      <meta name="description" content="Фудграм - О проекте" />
      <meta property="og:title" content="О проекте" />
    </MetaTags>
    
    <Container>
      <h1 className={styles.title}>Привет!</h1>
      <div className={styles.content}>
        <div>
          <h2 className={styles.subtitle}>Что это за сайт? </h2>
          <div className={styles.text}>
            <p className={styles.textItem}>
              Это выпускной проект Яндекс Практикума. Хоть он и являлся частью курса, создавался он без какой‑либо помощи.
            </p>
            <p className={styles.textItem}>
              Сутью проекта является создание и хранение рецептов на портале. Дополнительно можно скачать список продуотов для покупки, следить за рецептами друзей и сохранять рецепты в список любимых.
            </p>
            <p className={styles.textItem}>
              Создавайте аккаунт, хоть там и требуется почта, можете написать какой хотите, проверки не будет:) Кликайте кнопки, заливайте свои рецепты
            </p>
          </div>
        </div>
        <aside>
          <h2 className={styles.additionalTitle}>
            Ссылки
          </h2>
          <div className={styles.text}>
            <p className={styles.textItem}>
              Код проекта находится вот тут <a href="#" className={styles.textLink}>https://gitgub.com/Contrigra/foodgram-project</a>
            </p>
            <p className={styles.textItem}>
              И подписывайтесь на мой <a href="#" className={styles.textLink}>гитхаб</a>
            </p>
          </div>
        </aside>
      </div>
      
    </Container>
  </Main>
}

export default About

