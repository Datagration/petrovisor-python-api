import type { ReactNode } from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import Link from '@docusaurus/Link';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  logo: string;
  description: ReactNode;
  linkUrl: string;
};

const FeatureList: FeatureItem[] = [
  {
    title: '.NET SDK',
    logo: '/petrovisor-python-api/img/logos/dotnet-logo.svg',
    description: (
      <>
        REST API access with high-performance C# and ML.NET machine learning integration.
      </>
    ),
    linkUrl: 'https://www.nuget.org/packages/MyrConn.PetroVisor.Web.Client',
  },
  {
    title: 'R SDK',
    logo: '/petrovisor-python-api/img/logos/r-logo.svg',
    description: (
      <>
        REST API access with powerful statistical tools and data visualization.
      </>
    ),
    linkUrl: 'https://github.com/Datagration/petrovisor-r-api',
  },
  {
    title: 'Python SDK',
    logo: '/petrovisor-python-api/img/logos/python-logo.svg',
    description: (
      <>
        REST API access with versatile data processing and machine learning capabilities.
      </>
    ),
    linkUrl: 'https://pypi.org/project/petrovisor/',
  },
];

function Feature({ title, logo, description, linkUrl }: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <Link to={linkUrl} className={styles.cardLink}>
        <div className={styles.featureCard}>
          <div className={styles.cardHeader}>
            <div className={styles.logoWrapper}>
              <img src={logo} className={styles.featureLogo} alt={title} />
            </div>
            <Heading as="h3" className={styles.cardTitle}>
              {title}
            </Heading>
          </div>
          <div className={styles.cardBody}>
            <p>{description}</p>
          </div>
        </div>
      </Link>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
